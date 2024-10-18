/** @odoo-module */

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import {
  Component,
  xml,
  useState,
  onWillUpdateProps,
  onMounted,
  useRef,
  useEffect,
} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import GetDataComponent from "./getDataComponent";

class CustomWidget extends GetDataComponent {
  selectRef = useRef("select");
  setup() {
    super.setup();
    this.res_id = this.props.record.data.id;

    useEffect(
      () => {
        this.fetchData();

        return () => {};
      },
      () => []
    );
  }

  async fetchData() {
    const auto_action_id = await this.getAutoActions(this.res_id);
    if (auto_action_id.length) {
      const auto_action_type = auto_action_id[0].auto_action_type;

      console.log("auto_action_type: ", auto_action_type);
    }

    return () => {};
  }
}

CustomWidget.template = xml`
    <select t-ref="select" t-on-change="updateValue" style="border: none;">
    </select>
`;

CustomWidget.props = {
  ...standardFieldProps,
};
CustomWidget.supportedTypes = ["char"];

registry.category("fields").add("based_on", CustomWidget);
