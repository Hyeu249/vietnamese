/** @odoo-module */

import { standardFieldProps } from "@web/views/fields/standard_field_props"
import { Component, xml, useState, onWillUpdateProps, onMounted, useRef } from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"

const BOT_TELE_TOKEN = "7216628327:AAHPUtZJFDbsXY57rcrRC7HTmaxd3I55F9E"
const TELE_CHAT_ID = "-1002200424240"

class SendTelegramMessage extends Component {
    slideInterval = 3000
    slideTimer

    setup() {
        this.token = ""
        this.chat_id = ""
        this.res_id = this.props.record.data.id
        this.model_name = this.props.record.resModel
        this.orm = useService("orm")
        this.action = useService("action")

        this.set_token_and_chat_id()

        onWillUpdateProps((nextProps) => {
            const nextValue = nextProps.value
            if (nextValue !== this.props.value) {
                clearInterval(this.slideTimer)
                this.slideTimer = setInterval(() => {
                    this.sendTelegramMessageHandle(nextValue)
                    clearInterval(this.slideTimer)
                }, this.slideInterval)
            }
        })
    }

    async set_token_and_chat_id() {
        const function_name = "get_token_and_chat_id_based_on_company"
        const result = await this.orm.call("ship.tele.group.settings", function_name, [""], {})
        this.chat_id = result.chat_id
        this.token = result.token
    }

    async sendTelegramMessageHandle(nextValue) {
        const function_name = "get_is_allow_send_tele_message"
        const is_active_telegram = await this.orm.call("ship.tele.group.settings", function_name, [""], {})
        if (!is_active_telegram) return

        if (nextValue == "APPROVED" || nextValue == "REJECTED") {
            await this.removeTeleMessageByIdIfHave()
        } else {
            await this.removeTeleMessageByIdIfHave()
            const response_data = await this.send_to_telegram_message()

            if (response_data && response_data.ok) {
                this.update_message_id(response_data.result.message_id)
            }
        }
    }

    async send_to_telegram_message() {
        const text = await this.get_tele_sendMessage_data()
        const result = await this.sendMessage(text)

        return result
    }

    async get_tele_sendMessage_data() {
        const text = await this.orm.call(this.model_name, "get_tele_sendMessage_data", [this.res_id], {})

        return text
    }

    async update_message_id(message_id) {
        const response_data = await this.orm.call(this.model_name, "update_message_id", [this.res_id, message_id], {})
        return response_data
    }

    async sendMessage(text = "") {
        if (!this.token || !this.chat_id) return

        const url = `https://api.telegram.org/bot${this.token}/sendMessage`
        const params = {
            chat_id: this.chat_id,
            text: text,
            parse_mode: "Markdown",
        }

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(params),
            })

            const data = await response.json()
            return data
        } catch (error) {
            console.error("Error sending message:", error)
        }
    }

    async removeTeleMessageByIdIfHave() {
        if (!this.token || !this.chat_id) return

        const result = await this.orm.searchRead(this.model_name, [["id", "=", this.res_id]], ["message_id"])
        if (!result) return

        const message_id = result[0].message_id
        console.log("delete: ", message_id)
        const url = `https://api.telegram.org/bot${this.token}/deleteMessage`
        const params = {
            chat_id: this.chat_id,
            message_id: message_id,
        }

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(params),
            })

            const data = await response.json()
            return data
        } catch (error) {
            console.error("Error sending message:", error)
        }
    }
}

SendTelegramMessage.template = xml`
    <div></div>
`

SendTelegramMessage.props = {
    ...standardFieldProps,
}
SendTelegramMessage.supportedTypes = ["selection"]

registry.category("fields").add("sendTelegramMessage", SendTelegramMessage)
