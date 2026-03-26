#include <array>
#include <cstring>
#include <stdexcept>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <std_msgs/msg/int8.hpp>
#include <tf2/LinearMath/Quaternion.h>

#include <HD/hd.h>
#include <HDU/hduError.h>

class TouchNode : public rclcpp::Node {
public:
    TouchNode() : Node("touch_node") {
        publisher_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("/touch/pose", 10);
        button_publisher_ = this->create_publisher<std_msgs::msg::Int8>("/touch/buttons", 10);

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

        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(33),
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

        geometry_msgs::msg::PoseStamped msg;
        msg.header.stamp = this->get_clock()->now();
        msg.header.frame_id = "touch_base";

        // POSITION : on garde exactement ton mapping actuel
        msg.pose.position.x = current_data.position[2] / -100.0;
        msg.pose.position.y = current_data.position[0] / -100.0;
        msg.pose.position.z = current_data.position[1] / 100.0;

        // =========================
        // TEST ORIENTATION GIMBAL
        // =========================
        constexpr int GIMBAL_INDEX = 2;      // teste 0, puis 1, puis 2
        constexpr double GIMBAL_SIGN = 1.0;  // teste aussi -1.0

        const double angle = GIMBAL_SIGN * current_data.gimbal_angles[GIMBAL_INDEX];

        tf2::Quaternion q_test;

        // Test actuel : appliquer cet angle autour de Z
        q_test.setRPY(0.0, 0.0, angle);

        // Si Z n'est pas le bon axe, essaie à la place :
        // q_test.setRPY(angle, 0.0, 0.0); // autour de X
        // q_test.setRPY(0.0, angle, 0.0); // autour de Y

        q_test.normalize();

        msg.pose.orientation.w = q_test.w();
        msg.pose.orientation.x = q_test.x();
        msg.pose.orientation.y = q_test.y();
        msg.pose.orientation.z = q_test.z();

        publisher_->publish(msg);

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
            "pos=[%.3f %.3f %.3f] gimbal=[%.3f %.3f %.3f] angle=%.3f idx=%d sign=%.1f",
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z,
            current_data.gimbal_angles[0],
            current_data.gimbal_angles[1],
            current_data.gimbal_angles[2],
            angle,
            GIMBAL_INDEX,
            GIMBAL_SIGN
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
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<TouchNode>());
    rclcpp::shutdown();
    return 0;
}