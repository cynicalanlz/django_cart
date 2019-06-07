from collections import OrderedDict
from django.utils.translation import gettext as _
from django.forms.fields import MultipleHiddenInput, Field
from django.forms.widgets import ChoiceWidget
from django.forms import ValidationError
from django.forms import Form
from products.models import Product


class InputSelectMultiple(ChoiceWidget):
    allow_multiple_selected = True
    input_type = 'number'
    template_name = 'products/widgets/multiple_input.html'
    option_template_name = 'products/widgets/input_option.html'

    def __init__(self, attrs=None, product_fields=()):
        super().__init__(attrs)
        # choices can be any iterable, but we may need to render this widget
        # multiple times. Thus, collapse it into a list so it can be consumed
        # more than once.
        self.product_fields = product_fields


    def optgroups(self, name, value, attrs=None):
        """Return a list of optgroups for this widget."""
        options = []

        for index, (name, product_data) in enumerate(self.product_fields.items()):
            quantity = product_data['quantity']
            name = product_data['name']
            price = product_data['price']
            if index:
                label = 'product_{}'.format(str(index))
            else:
                label =  'product'

            options.append({
                'value': quantity,
                'price': price,
                'name': 'products',
                'label': name,
                'type': self.input_type,
                'template_name': self.option_template_name,
                'wrap_label': True,
                'index': index
            })

        return options

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False

    def value_omitted_from_data(self, data, files, name):
        # HTML checkboxes don't appear in POST data if not checked, so it's
        # never known if the value is actually omitted.
        return False

    def id_for_label(self, id_, index=None):
        """"
        Don't include for="field_0" in <label> because clicking such a label
        would toggle the first checkbox.
        """
        if index is None:
            return ''
        return super().id_for_label(id_, index)


class ProductModelMultipleChoiceField(Field):
    hidden_widget = MultipleHiddenInput
    widget = InputSelectMultiple
    default_error_messages = {
        'out_of_stock': _('I’m sorry but we are out of stock for {}'),
        'less_quantity': _('I’m sorry but we only have {} of {} left'),
        'incorrect_quantity': _('Entered value for {} is <= 0.'),
        'invalid_list': _('Enter a list of values.'),
    }

    def __init__(self, *,  queryset=(),  **kwargs):
        super().__init__(**kwargs)
        self.queryset = queryset
        self.validation_counter = 0
        self.product_fields = OrderedDict(**{
            product['id']: {
                'quantity': product['quantity'],
                'name': product['name'],
                'price': product['price']
            } for product in queryset.values('id',
                                             'quantity',
                                             'name',
                                             'price')
        })

    def _get_product_fields(self):
        return self._product_fields

    def _set_product_fields(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        self._product_fields = self.widget.product_fields = value

    product_fields = property(_get_product_fields,
                              _set_product_fields)

    def to_python(self, value):
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['invalid_list'], code='invalid_list')
        return [str(val) for val in value]

    def validate(self, value):
        """Validate that the input is a list or tuple."""

        current_values = dict(self.queryset.values_list('id', 'quantity'))
        for product_id in self.product_fields.keys():
            self.product_fields[product_id]['quantity'] = current_values[product_id]

        errors = []
        for (product_id, product_data), chosen_value in zip(self.product_fields.items(), value):
            name = product_data['name']
            int_chosen_val = int(chosen_value)
            if product_data['quantity'] == 0:
                errors.append(
                    ValidationError(self.error_messages['out_of_stock'].format(name))
                )
                continue
            if int_chosen_val <= 0:
                errors.append(
                    ValidationError(self.error_messages['incorrect_quantity'].format(name))
                )
                continue

            if product_data['quantity'] < int_chosen_val:
                errors.append(
                    ValidationError(self.error_messages['less_quantity'].format(product_data['quantity'], name))
                )
                continue

        if len(errors) > 0:
            raise ValidationError(errors)


    def has_changed(self, initial, data):
        if self.disabled:
            return False
        if initial is None:
            initial = []
        if data is None:
            data = []
        if len(initial) != len(data):
            return True
        initial_set = {str(value) for value in initial}
        data_set = {str(value) for value in data}
        return data_set != initial_set


class ShoppingCartForm(Form):

    products = ProductModelMultipleChoiceField(queryset=Product.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)