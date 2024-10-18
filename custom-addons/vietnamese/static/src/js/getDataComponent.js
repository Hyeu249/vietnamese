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

export default class CustomWidget extends Component {
  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
  }

  async getTables(table_ids, return_values = ["field_ids"]) {
    return this.orm.searchRead(
      "vietnamese.table",
      [["id", "=", table_ids]],
      return_values
    );
  }

  async getFields(
    field_ids,
    return_values = ["id", "name", "field_description", "ttype"]
  ) {
    return this.orm.searchRead(
      "ir.model.fields",
      [["id", "=", field_ids]],
      return_values
    );
  }

  async getAutoActions(ids, return_values = ["auto_action_type"]) {
    return this.orm.searchRead(
      "base.automation",
      [["id", "=", ids]],
      return_values
    );
  }

  updateValue(event) {
    const value = event.target.value;
    this.props.update(value);
  }
}
