from odoo.exceptions import ValidationError


class ListenTemplate:
    def __init__(self):
        self._callback_create = []
        self._callback_writer = {}
        self._callback_unlink = []
        self.relations = []

    def on_create(self, function):
        message = f"Tên callback function phải unique cho on_create, vui lòng đặt lại!"

        func_name = function.__name__
        func_names = self._callback_create

        if func_name in func_names:
            raise ValidationError(f"{function}-{message}-{func_names}")

        self._callback_create.append(function.__name__)

        def wrapper(*args, **kwargs):
            function(*args, **kwargs)

        return wrapper

    def on_unlink(self, function):
        message = f"Tên callback function phải unique cho on_unlink, vui lòng đặt lại!"

        func_name = function.__name__
        func_names = self._callback_unlink

        if func_name in func_names:
            raise ValidationError(f"{function}-{message}")

        self._callback_unlink.append(function.__name__)

        def wrapper(*args, **kwargs):
            function(*args, **kwargs)

        return wrapper

    def on_write(self, *args):
        """Return a decorator to decorate an on_write method for given fields."""
        message = f"Tên callback function phải unique cho on_write, vui lòng đặt lại!"

        def decorate(function):
            func_name = function.__name__
            func_names = self._callback_writer.keys()

            if func_name in func_names:
                raise ValidationError(f"{function}-{message}")

            self._callback_writer[function.__name__] = args

            def wrapper(*args, **kwargs):
                function(*args, **kwargs)

            return wrapper

        return decorate

    def call_on_create(self, records):
        for record in records:
            for func_name in self._callback_create:
                relation_dot_func = self.get_func_from_its_relation_to_call(
                    record, func_name
                )
                relation_dot_func()

    def call_on_write(self, records, vals):
        for record in records:
            for func_name, fields in self._callback_writer.items():
                any_field_in_vals = any([field in vals for field in fields])
                if any_field_in_vals:
                    model_dot_func = self.get_func_from_its_relation_to_call(
                        record, func_name
                    )
                    model_dot_func()

    def get_funcs_to_call_after_unlink(self, records):
        functions = []
        for record in records:
            for func_name in self._callback_unlink:
                relation_dot_func = self.get_func_from_its_relation_to_call(
                    record, func_name
                )
                functions.append(relation_dot_func)

        return functions

    def get_func_from_its_relation_to_call(self, record, func_name):

        relation = self.get_relation_by_record_and_func_name(record, func_name)
        func = getattr(relation, func_name)

        return func

    def get_relation_by_record_and_func_name(self, record, func_name):

        for relation_name in self.relations:
            relation = record[relation_name]

            if getattr(relation, func_name, False):
                return relation

        return record


class Job_quote(ListenTemplate):
    def __init__(self):
        super().__init__()
        self.relations = [
            "maintenance_scope_report_id",
            "job_id",
            "job_supplier_quote_id",
            "job_supplier_quote_ids",
            "material_assignment_ids",
            "area_of_paint_job_ids",
        ]


class JobSupplierQuote(ListenTemplate):
    def __init__(self):
        super().__init__()
        self.relations = [
            "supplier_id",
            "job_quote_id",
        ]


job_quote = Job_quote()
job_supplier_quote = JobSupplierQuote()
