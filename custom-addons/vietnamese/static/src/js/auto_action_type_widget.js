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
    this.table_id = this.props?.record?.context?.table_id;
    super.setup();

    useEffect(
      () => {
        this.fetchData();

        return () => {};
      },
      () => []
    );
  }

  async fetchData() {
    const tables = await this.getTables(this.table_id);
    if (tables.length) {
      const field_ids = tables[0].field_ids;

      if (field_ids.length) {
        const option_tags = await this.getDefautValueOptions(field_ids);

        this.selectRef.el.innerHTML = option_tags.length
          ? "<option value=''></option>" + option_tags.join()
          : `<option></option>`;
      }
    }

    return () => {};
  }

  async getDefautValueOptions(field_ids) {
    const fields_data = await this.getFields(field_ids);
    const relation_field = (e) => ["one2many", "many2one"].includes(e.ttype);

    return fields_data.filter(relation_field).map((field) => {
      const value =
        `on_create__set_default_value_for_${field.ttype}__` + field.id;
      const label = "Tạo giá trị mặc định cho " + field.field_description;
      const selected = value === this.props.value ? "selected" : null;

      return `
            <option value="${value}" ${selected ? "selected" : ""}>
                ${label}
            </option>
          `;
    });
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

registry.category("fields").add("auto_action_type", CustomWidget);
