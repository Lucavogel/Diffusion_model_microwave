#include <array>
#include <cstring>
#include <stdexcept>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <std_msgs/msg/int8.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Matrix3x3.h>
#include <tf2_ros/transform_broadcaster.h>
#include <geometry_msgs/msg/transform_stamped.hpp>

#include <HD/hd.h>
#include <HDU/hduError.h>

class TouchNode : public rclcpp::Node {
public:
    TouchNode() : Node("orientation_test") {
        publisher_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("/touch/pose", 10);
        button_publisher_ = this->create_publisher<std_msgs::msg::Int8>("/touch/buttons", 10);
        tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);

        hHD_ = hdInitDevice(HD_DEFAULT_DEVICE);
        if (HD_DEVICE_ERROR(error_ = hdGetError())) {
            hduPrintError(stderr, &error_, "Failed to initialize Touch device");
            throw std::runtime_error("hdInitDevice failed");
        }

        callback_handle_ = hdScheduleAsynchronous(
            updateDeviceCallback,
            this,
            HD_MAX_SCHEDULER_PRIORITY
        );

        hdStartScheduler();
        if (HD_DEVICE_ERROR(error_ = hdGetError())) {
            hduPrintError(stderr, &error_, "Failed to start scheduler");
            throw std::runtime_error("hdStartScheduler failed");
        }

        scheduler_started_ = true;

        // On réduit le délai à 5ms (soit 200 Hz au lieu de ~30 Hz à 33ms) pour tuer la latence
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(10),
            std::bind(&TouchNode::publish_pose, this)
        );

        RCLCPP_INFO(this->get_logger(), "Touch Node demarre sur /touch/pose");
    }

    ~TouchNode() override {
        if (scheduler_started_) {
            hdStopScheduler();
            scheduler_started_ = false;
        }

        if (callback_handle_ != HD_INVALID_HANDLE) {
            hdUnschedule(callback_handle_);
            callback_handle_ = HD_INVALID_HANDLE;
        }

        if (hHD_ != HD_INVALID_HANDLE) {
            hdDisableDevice(hHD_);
            hHD_ = HD_INVALID_HANDLE;
        }
    }

private:
    struct DeviceData {
        HDint buttons = 0;
        HDdouble position[3] = {0.0, 0.0, 0.0};
        HDdouble gimbal_angles[3] = {0.0, 0.0, 0.0};
        HDdouble joint_angles[3] = {0.0, 0.0, 0.0};
        HDdouble transform[16] = {};
        HDErrorInfo error{};
        bool valid = false;
    };

    struct CopyUserData {
        DeviceData *dst;
        DeviceData *src;
    };

    static HDCallbackCode HDCALLBACK updateDeviceCallback(void *pUserData) {
        auto *self = static_cast<TouchNode *>(pUserData);

        hdBeginFrame(hdGetCurrentDevice());

        hdGetIntegerv(HD_CURRENT_BUTTONS, &self->servo_data_.buttons);
        hdGetDoublev(HD_CURRENT_POSITION, self->servo_data_.position);
        hdGetDoublev(HD_CURRENT_GIMBAL_ANGLES, self->servo_data_.gimbal_angles);
        hdGetDoublev(HD_CURRENT_JOINT_ANGLES, self->servo_data_.joint_angles);

        self->servo_data_.error = hdGetError();
        self->servo_data_.valid = !HD_DEVICE_ERROR(self->servo_data_.error);

        hdGetDoublev(HD_CURRENT_TRANSFORM, self->servo_data_.transform);

        hdEndFrame(hdGetCurrentDevice());

        return HD_CALLBACK_CONTINUE;
    }

    static HDCallbackCode HDCALLBACK copyDeviceDataCallback(void *pUserData) {
        auto *copy_data = static_cast<CopyUserData *>(pUserData);
        std::memcpy(copy_data->dst, copy_data->src, sizeof(DeviceData));
        return HD_CALLBACK_DONE;
    }

    void publish_pose() {
        DeviceData current_data;
        CopyUserData copy_args{&current_data, &servo_data_};

        hdScheduleSynchronous(
            copyDeviceDataCallback,
            &copy_args,
            HD_MIN_SCHEDULER_PRIORITY
        );

        if (!current_data.valid) {
            if (HD_DEVICE_ERROR(current_data.error)) {
                RCLCPP_WARN_THROTTLE(
                    this->get_logger(),
                    *this->get_clock(),
                    2000,
                    "Erreur device detectee, aucune nouvelle pose valide."
                );

                if (hduIsSchedulerError(&current_data.error)) {
                    RCLCPP_ERROR_THROTTLE(
                        this->get_logger(),
                        *this->get_clock(),
                        2000,
                        "Erreur scheduler OpenHaptics."
                    );
                }
            }
            return;
        }

                // colonne 0
        double r00 = current_data.transform[0];
        double r10 = current_data.transform[1];
        double r20 = current_data.transform[2];

        // colonne 1
        double r01 = current_data.transform[4];
        double r11 = current_data.transform[5];
        double r21 = current_data.transform[6];

        // colonne 2
        double r02 = current_data.transform[8];
        double r12 = current_data.transform[9];
        double r22 = current_data.transform[10];

        tf2::Matrix3x3 R_raw(
            r00, r01, r02,
            r10, r11, r12,
            r20, r21, r22
        );

        // 1. Aligner les axes ! (Ton code avait la matrice identité ici)
        // Position du code : X_ros = Z_touch, Y_ros = X_touch, Z_ros = Y_touch
        tf2::Matrix3x3 R_mapping(
            0, 0, 1,
            1, 0, 0,
            0, 1, 0
        );

        // 2. Transformer la rotation brute du Touch dans le monde ROS
        tf2::Matrix3x3 R_base = R_mapping * R_raw;

        // 3. Correction LOCALE du stylet (pour aligner l'axe rouge 'X' de RViz avec la pointe physique du stylet)
        tf2::Matrix3x3 R_fix;
   
        R_fix.setRPY(0.0, 1.57079632679, 3.14159265359); 

        tf2::Matrix3x3 R_corrected = R_base * R_fix;

        tf2::Quaternion q;
        R_corrected.getRotation(q);
        q.normalize();

        geometry_msgs::msg::PoseStamped msg;
        msg.header.stamp = this->get_clock()->now();
        msg.header.frame_id = "world"; // On met "world" pour que RViz puisse l'afficher sans erreur de TF


        // POSITION : on garde exactement ton mapping actuel
        msg.pose.position.x = current_data.position[2] / 100.0;
        msg.pose.position.y = current_data.position[0] / 100.0;
        msg.pose.position.z = current_data.position[1] / 100.0;

        // ORIENTATION
        msg.pose.orientation.w = q.w();
        msg.pose.orientation.x = q.x();
        msg.pose.orientation.y = q.y();
        msg.pose.orientation.z = q.z();

        publisher_->publish(msg);

        // Publication TF pour le voir en live sous RViz
        geometry_msgs::msg::TransformStamped t;
        t.header.stamp = msg.header.stamp;
        t.header.frame_id = "world";  // Frame global sous rviz
        t.child_frame_id = "touch_cursor";
        t.transform.translation.x = msg.pose.position.x;
        t.transform.translation.y = msg.pose.position.y;
        t.transform.translation.z = msg.pose.position.z;
        t.transform.rotation = msg.pose.orientation;
        
        if (tf_broadcaster_) {
            tf_broadcaster_->sendTransform(t);
        }

        std_msgs::msg::Int8 button_msg;
        const bool b1 = (current_data.buttons & HD_DEVICE_BUTTON_1) != 0;
        const bool b2 = (current_data.buttons & HD_DEVICE_BUTTON_2) != 0;

        if (b1 && b2) {
            button_msg.data = 2;
        } else if (b1) {
            button_msg.data = 1;
        } else if (b2) {
            button_msg.data = -1;
        } else {
            button_msg.data = 0;
        }

        button_publisher_->publish(button_msg);

        RCLCPP_INFO_THROTTLE(
            this->get_logger(),
            *this->get_clock(),
            1000,
            "pos=[%.3f %.3f %.3f] gimbal=[%.3f %.3f %.3f]",
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z,
            current_data.gimbal_angles[0],
            current_data.gimbal_angles[1],
            current_data.gimbal_angles[2]
        
        );
    }

    HHD hHD_ = HD_INVALID_HANDLE;
    HDSchedulerHandle callback_handle_ = HD_INVALID_HANDLE;
    bool scheduler_started_ = false;
    HDErrorInfo error_{};

    DeviceData servo_data_{};

    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr publisher_;
    rclcpp::Publisher<std_msgs::msg::Int8>::SharedPtr button_publisher_;
    std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<TouchNode>());
    rclcpp::shutdown();
    return 0;
}