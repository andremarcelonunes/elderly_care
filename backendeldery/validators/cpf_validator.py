import re
from typing import Annotated
from pydantic import GetPydanticSchema, GetCoreSchemaHandler
from pydantic_core import PydanticCustomError, core_schema


def validate_cpf_format(
    v: str,
    handler: core_schema.ValidatorFunctionWrapHandler,
    info: core_schema.ValidationInfo,
) -> str:
    """Validates and formats CPF"""
    if v is None:
        return handler(None)

    # Remove non-numeric characters
    cpf = re.sub(r"[^\d]", "", v)

    # Check if it has 11 digits
    if len(cpf) != 11:
        raise PydanticCustomError("cpf_format", "CPF deve conter 11 dígitos")

    # Format CPF
    formatted_cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    # Check format
    if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", formatted_cpf):
        raise PydanticCustomError(
            "cpf_format", "CPF deve estar no formato xxx.xxx.xxx-xx"
        )

    return handler(formatted_cpf)


class CPFValidator:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_wrap_validator_function(
            function=validate_cpf_format,
            schema=core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )
