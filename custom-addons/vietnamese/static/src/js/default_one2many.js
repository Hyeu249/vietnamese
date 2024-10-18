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

class CustomWidget extends Component {
  selectRef = useRef("select");
  setup() {
    this.ttype = this.props?.record?.data?.ttype;
    this.relation = this.props?.record?.data?.relation;
    this.name = this.props?.record?.data?.name;
    this.field_description = this.props?.record?.data?.field_description;
    this.relation_field = this.props?.record?.data?.relation_field;
    this.orm = useService("orm");
    this.action = useService("action");

    useEffect(
      () => {
        this.fetchData();

        return () => {};
      },
      () => []
    );
  }

  async fetchData() {
    if (this.ttype !== "one2many") return;
    const option_tags = await this.getOptions();

    this.selectRef.el.innerHTML = option_tags.length
      ? "<option value=''></option>" + option_tags.join()
      : `<option></option>`;

    return () => {};
  }

  async getOptions() {
    const fields = await this.get_fields_from_relation_table();
    const filtered_fields = fields.filter(
      (e) => e.ttype === "many2one" && e.name !== this.relation_field
    );

    const options = filtered_fields.map((field) => {
      const value = `on_create__create_default_value_for__${this.name}__based_on__${field.name}`;
      const label = `Tạo giá trị mặc định cho '${this.field_description}' dựa trên trường '${field.field_description}'`;
      const selected = value === this.props.value ? "selected" : null;

      return `
      <option value="${value}" ${selected ? "selected" : ""}>
        ${label}
      </option>
      `;
    });

    return options;
  }

  async get_relation_table() {
    const relation_table_s = await this.orm.searchRead(
      "vietnamese.table",
      [["model", "=", this.relation]],
      ["id", "field_ids"]
    );

    if (relation_table_s.length) return relation_table_s[0];
  }

  async get_fields_from_relation_table() {
    const relation_table = await this.get_relation_table();

    const fields = await this.orm.searchRead(
      "ir.model.fields",
      [["id", "=", relation_table.field_ids]],
      ["id", "field_description", "ttype", "name", "relation"]
    );

    if (fields.length) return fields;
  }

  updateValue(event) {
    const value = event.target.value;
    this.props.update(value);
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

registry.category("fields").add("default_one2many", CustomWidget);
