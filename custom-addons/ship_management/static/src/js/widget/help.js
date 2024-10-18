/** @odoo-module */

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import {
  Component,
  xml,
  useState,
  onWillUpdateProps,
  onMounted,
  useEffect,
  useRef,
} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class HelpField extends Component {
  content = useRef("content");
  setup() {
    useEffect(
      () => {
        this.content.el.innerHTML = this.props.value;

        return () => {};
      },
      () => []
    );
  }
}

HelpField.template = xml`
    <div class="help-container">
        <button class="help-button">Hướng dẫn</button>
        <div class="help-content">
            <p t-ref="content"></p>
        </div>
    </div>
`;

HelpField.props = {
  ...standardFieldProps,
};
HelpField.supportedTypes = ["char"];

registry.category("fields").add("help_field", HelpField);
