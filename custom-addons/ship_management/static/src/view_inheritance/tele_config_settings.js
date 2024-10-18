/** @odoo-module */

import { registry } from "@web/core/registry"
import { listView } from "@web/views/list/list_view"
import { ListController } from "@web/views/list/list_controller"
import { useService } from "@web/core/utils/hooks"

class ModelListController extends ListController {
    setup() {
        super.setup()
        this.orm = useService("orm")
        this.action = useService("action")
    }

    async getTeleChatIds() {
        const token = await this.orm.call("ship.tele.group.settings", "get_tele_token", [""], {})
        const data = await this.getTelegramUpdates(token)

        if (data && data.ok) {
            const result = data.result
            const newData = result.map((object) => {
                for (const [_, value] of Object.entries(object)) {
                    console.log()
                    if (value.chat?.id) return [value.chat.id, value.chat.title]
                }
            })

            const unique_id = [...new Set(newData.map((e) => e[0]))]
            const unique_group = this.getUniqueArray(newData)

            const text_arr = unique_group.map((e) => `${e[0]}: ${e[1]}`)

            alert(text_arr.join("\n"))

            console.log("unique_id: ", unique_id)
            console.log("unique_group: ", unique_group)
            console.log("data: ", data)
        }

        await this.loadResource()
    }

    getUniqueArray(arr) {
        const seen = new Set()
        return arr.filter((item) => {
            const key = JSON.stringify(item)
            return seen.has(key) ? false : seen.add(key)
        })
    }

    async getTelegramUpdates(token) {
        const URL = `https://api.telegram.org/bot${token}/getUpdates`
        try {
            const response = await fetch(URL)
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`)
            }
            const data = await response.json()
            return data
        } catch (error) {
            console.error("Failed to fetch updates:", error)
        }
    }

    async loadResource() {
        // await this.props.record.model.root.load()
        // await this.props.record.model.notify()
    }
}

export const modelListView = {
    ...listView,
    Controller: ModelListController,
    buttonTemplate: "owl.TeleConfigSettingsListView.Buttons",
}

registry.category("views").add("tele_config_settings_list_view", modelListView)
