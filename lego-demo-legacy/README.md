# LEGO Demo Legacy System

Mini sistema legacy para demo de LEGO: Legacy Business Logic Recovery.

## Caso funcional

Proceso batch diario de validacion de pagos.

El JCL `RUN_PAYMENTS_DAILY.jcl` ejecuta `PAYMAIN`, que orquesta validaciones en subprogramas COBOL:

- `CUSTVAL`: valida cliente, estado y KYC.
- `BALCHK`: valida cuenta, divisa, saldo y limite diario.
- `RISKSCOR`: calcula score de riesgo.
- `TXNLOG`: genera linea de auditoria.

## Reglas de negocio esperadas

1. Si el cliente no existe o esta bloqueado, se rechaza el pago.
2. Si KYC esta incompleto, se rechaza el pago.
3. Si la cuenta esta bloqueada o cerrada, se rechaza el pago.
4. Si la moneda del pago no coincide con la cuenta, se rechaza el pago.
5. Si el pago supera el limite diario, queda en revision.
6. Si el pago supera el saldo, se rechaza por fondos insuficientes.
7. Si el score de riesgo supera 80, se rechaza.
8. Si el score de riesgo supera 60, queda en revision manual.
9. Si todas las validaciones pasan, se aprueba y se audita.

## Por que funciona bien para demo

Incluye JCL, programa principal, subprogramas, copybooks, datos de entrada, datasets y flujo batch end-to-end.
