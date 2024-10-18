/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { HelpController } from "./help_controller";

class ModelListController extends HelpController {
  setup() {
    super.setup();
    this.model_name = "ship.material.paint.quotes.request";
    this.action = useService("action");
  }

  async openHelp() {
    const default_value_ids = await this.getDefaultValueIdsBasedOnModelName(
      this.model_name
    );
    const cron_ids = await this.getCronIdsBasedOnModelName(this.model_name);
    const cron2_ids = await this.getCronIdsBasedOnModelName(
      "ship.supplier.quote.portal.change.notification"
    );
    const cron3_ids = await this.getCronIdsBasedOnModelName("mail.mail");

    await this.action.doAction({
      type: "ir.actions.act_window",
      name: "Help",
      res_model: "ship.help.wiz",
      view_mode: "form",
      target: "new",
      views: [[false, "form"]],
      context: {
        default_default_value_ids: default_value_ids,
        default_cron_ids: [...cron_ids, ...cron2_ids, ...cron3_ids],
        default_help: `
                1.Đại phó, máy trưởng vào phần mềm, tạo yêu cầu cấp vật tư, sơn<br>
                2.Chọn ngày yêu cầu giao hàng, và thời hạn<br>
                3.Chọn báo giá vật tư, phụ tùng hoặc sơn(có nút thêm mới khi không thấy)<br>
                4.Duyệt lên các cấp có liên quan sau khi hoàn thành việc chọn vật tư để mua<br>
                5.Sau khi các nhà cung cấp hoàn thành báo giá hoặc hết thời hạn, tầng duyệt tự động đẩy lên 1 bậc<br>
                6.Sau khi được CEO duyệt, các bên có liên quan nhập vật tư vào phần mềm khi đã nhận(có nút nhận vật tư, và số lượng đã nhận)<br>
            `,
      },
    });
  }
}

export const modelListView = {
  ...listView,
  Controller: ModelListController,
  buttonTemplate: "owl.MaterialPaintQuotesRequestListView.Buttons",
};

registry
  .category("views")
  .add("material_paint_quotes_request_list_view", modelListView);
