import time

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from client import client

user_open_ids = ["ou_1df9a3dc271bf2f3f51990f8a06f2bf6"]


# 获取会话历史消息
def list_chat_history(chat_id: str) -> None:
    request = ListMessageRequest.builder() \
        .container_id_type("chat") \
        .container_id(chat_id) \
        .build()

    response = client.im.v1.message.list(request)

    if not response.success():
        raise Exception(
            f"client.im.v1.message.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

    f = open(f"./chat_history.txt", "w")
    for i in response.data.items:
        sender_id = i.sender.id
        create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(i.create_time) / 1000))
        content = i.body.content

        msg = f"chatter({sender_id}) at {create_time} send: {content}"
        f.write(msg + "\n")

    f.close()


# 创建报警群并拉人入群
def create_alert_chat() -> str:
    request = CreateChatRequest.builder() \
        .user_id_type("open_id") \
        .request_body(CreateChatRequestBody.builder()
                      .name("P0: Nhóm cảnh báo của tôi")
                      .description("Mô tả nhóm cảnh báo")
                      .user_id_list(user_open_ids)
                      .build()) \
        .build()

    response = client.im.v1.chat.create(request)

    if not response.success():
        raise Exception(
            f"client.im.v1.chat.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

    return response.data.chat_id


# 发送报警消息
def send_alert_message(chat_id: str) -> None:
    request = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("interactive")
                      .content(_build_card("Theo dõi"))
                      .build()) \
        .build()

    response = client.im.v1.chat.create(request)

    if not response.success():
        raise Exception(
            f"client.im.v1.chat.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")


# 上传图片
def _upload_image() -> str:
    file = open("alert.png", "rb")
    request = CreateImageRequest.builder() \
        .request_body(CreateImageRequestBody.builder()
                      .image_type("message")
                      .image(file)
                      .build()) \
        .build()

    response = client.im.v1.image.create(request)

    if not response.success():
        raise Exception(
            f"client.im.v1.image.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

    return response.data.image_key


# 获取会话信息
def get_chat_info(chat_id: str) -> GetChatResponseBody:
    request = GetChatRequest.builder() \
        .chat_id(chat_id) \
        .build()

    response = client.im.v1.chat.get(request)

    if not response.success():
        raise Exception(
            f"client.im.v1.chat.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

    return response.data


# 更新会话名称
def update_chat_name(chat_id: str, chat_name: str):
    request: UpdateChatRequest = UpdateChatRequest.builder() \
        .chat_id(chat_id) \
        .request_body(UpdateChatRequestBody.builder()
                      .name(chat_name)
                      .build()) \
        .build()

    response: UpdateChatResponse = client.im.v1.chat.update(request)

    if not response.success():
        raise Exception(
            f"client.im.v1.chat.update failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")


# 处理消息回调
def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    msg = data.event.message
    if "/solve" in msg.content:
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(msg.chat_id)
                          .msg_type("text")
                          .content("{\"text\":\"Vấn đề đã được giải quyết, cảm ơn!\"}")
                          .build()) \
            .build()

        response = client.im.v1.chat.create(request)

        if not response.success():
            raise Exception(
                f"client.im.v1.chat.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

        # 获取会话信息
        chat_info = get_chat_info(msg.chat_id)
        name = chat_info.name
        if name.startswith("[跟进中]"):
            name = "[Đã giải quyết]" + name[5:]
        elif not name.startswith("[Đã giải quyết]"):
            name = "[Đã giải quyết]" + name

        # 更新会话名称
        update_chat_name(msg.chat_id, name)


# 处理卡片回调
def do_interactive_card(data: lark.Card) -> Any:
    if data.action.value.get("key") == "follow":
        # 获取会话信息
        chat_info = get_chat_info(data.open_chat_id)
        name = chat_info.name
        if not name.startswith("[跟进中]") and not name.startswith("[Đã giải quyết]"):
            name = "[Theo dõi] " + name

        # 更新会话名称
        update_chat_name(data.open_chat_id, name)

        return _build_card("Theo dõi")


# 构建卡片
def _build_card(button_name: str) -> str:
    image_key = _upload_image()
    card = {
        "config": {
            "wide_screen_mode": True
        },
        "header": {
            "template": "red",
            "title": {
                "tag": "plain_text",
                "content": "Báo động cấp 1 - Nền tảng dữ liệu"
            }
        },
        "elements": [
            {
                "tag": "div",
                "fields": [
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "**🕐 Thời gian:**\n2021-02-23 20:17:51"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "**🔢ID sự kiện:**\n336720"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "**📋 Dự án:**\nQA 7"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "**👤 Nhân viên trực cấp 1:**\n<at id=all>tất cả mọi người</at>"
                        }
                    },
                    {
                        "is_short": True,
                        "text": {
                            "tag": "lark_md",
                            "content": "**👤 Nhân viên trực cấp 2:**\n<at id=all>tất cả mọi người</at>"
                        }
                    },
                ]
            },
            {
                "tag": "img",
                "img_key": image_key,
                "alt": {
                    "tag": "plain_text",
                    "content": " "
                },
                "title": {
                    "tag": "lark_md",
                    "content": "Phương thức thanh toán tỷ lệ thành công dưới 50%:"
                }
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "🔴 Số lượng thanh toán thất bại  🔵 Số lượng thanh toán thành công"
                    }
                ]
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": button_name
                        },
                        "type": "primary",
                        "value": {
                            "key": "follow"
                        },
                    },
                    {
                        "tag": "select_static",
                        "placeholder": {
                            "tag": "plain_text",
                            "content": "Tạm thời ẩn"
                        },
                        "options": [
                            {
                                "text": {
                                    "tag": "plain_text",
                                    "content": "Ẩn 10 phút"
                                },
                                "value": "1"
                            },
                            {
                                "text": {
                                    "tag": "plain_text",
                                    "content": "Ẩn 30 phút"
                                },
                                "value": "2"
                            },
                            {
                                "text": {
                                    "tag": "plain_text",
                                    "content": "Ẩn 1 giờ"
                                },
                                "value": "3"
                            },
                            {
                                "text": {
                                    "tag": "plain_text",
                                    "content": "Ẩn 24 giờ"
                                },
                                "value": "4"
                            },
                        ],
                        "value": {
                            "key": "value"
                        }
                    }
                ]
            },
            {
                "tag": "hr"
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "🙋🏼 [Tôi muốn phản hồi cảnh báo sai](https://open.feishu.cn/) | 📝 [Ghi nhận quá trình xử lý cảnh báo](https://open.feishu.cn/)"
                }
            }
        ]
    }

    return lark.JSON.marshal(card)