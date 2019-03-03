from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ValidationError


class NotEnoughMoneyValidationError(ValidationError):
    """
    继承自 ValidationError,购买商品时金币不够的报这个错误
    """
    default_detail = _('need more coin.')
    default_code = 'invalid'
