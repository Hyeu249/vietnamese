/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";

export class HelpController extends ListController {
  setup() {
    super.setup();
    this.orm = useService("orm");
  }

  async getDefaultValueIdsBasedOnModelName(model_name) {
    const result = await this.orm.searchRead("utilities.default.value", []);
    if (result.length) {
      const default_value_ids = result.filter((result) => {
        return result.variable_name.split("_")[1].toLowerCase() == model_name;
      });
      return default_value_ids.map((result) => result.id);
    } else return [];
  }

  async getCronIdsBasedOnModelName(model_name) {
    const model_ids = await this.orm.searchRead(
      "ir.model",
      [["model", "=", model_name]],
      ["id"]
    );

    if (model_ids.length > 0) {
      const model_id = model_ids[0].id;
      const cron_ids = await this.orm.searchRead(
        "ir.cron",
        [["model_id", "=", model_id]],
        ["id"]
      );

      return cron_ids.map((result) => result.id);
    } else {
      return [];
    }
  }
}
