/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { HelpController } from "./help_controller";

class ModelListController extends HelpController {
  setup() {
    super.setup();
    this.model_name = "ship.inspection.plan";
    this.action = useService("action");
  }

  async openHelp() {
    const default_value_ids = await this.getDefaultValueIdsBasedOnModelName(
      this.model_name
    );
    const cron_ids = await this.getCronIdsBasedOnModelName(this.model_name);

    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Help",
      res_model: "ship.help.wiz",
      view_mode: "form",
      target: "new",
      views: [[false, "form"]],
      context: {
        default_default_value_ids: default_value_ids,
        default_cron_ids: cron_ids,
        default_help: `
                1.<br>
                2.<br>
                3.<br>
                4.<br>
                5.
            `,
      },
    });
  }
}

export const modelListView = {
  ...listView,
  Controller: ModelListController,
  buttonTemplate: "owl.InspectionPlanListView.Buttons",
};

registry.category("views").add("inspection_plan_list_view", modelListView);
