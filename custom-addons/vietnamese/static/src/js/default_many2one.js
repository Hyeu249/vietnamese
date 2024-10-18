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

class CustomWidget extends Component {
  selectRef = useRef("select");
  setup() {
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
    const many2oneRecords = await this.orm.searchRead(
      this.props?.record?.data?.relation,
      [],
      ["id", "x_name"]
    );
    if (many2oneRecords.length) {
      const option_tags = await this.getRecordOptions(many2oneRecords);

      this.selectRef.el.innerHTML = option_tags.length
        ? "<option value=''></option>" + option_tags.join()
        : `<option></option>`;
    }

    return () => {};
  }

  async getRecordOptions(records) {
    return records.map((field) => {
      const value = field.id;
      const selected = value === this.props.value ? "selected" : null;

      return `
            <option value="${value}" ${selected ? "selected" : ""}>
                ${field.x_name}
            </option>
          `;
    });
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

registry.category("fields").add("default_many2one", CustomWidget);
