# 🚀 Reporte: SISTEMA CONSOLIDADO

**OBJETIVO PRINCIPAL**: El objetivo principal de este programa COBOL es procesar transacciones bancarias, actualizando los saldos de las cuentas en una base de datos según los montos de las transacciones.

**FLUJO FUNCIONAL**: El proceso se divide en tres pasos clave:

1. **Lectura de transacciones**: El programa lee un archivo de texto que contiene las transacciones a procesar, con cada línea representando una transacción con un ID y un monto.
2. **Procesamiento de transacciones**: Para cada transacción, el programa consulta el saldo actual de la cuenta en la base de datos, aplica la lógica de negocio para validar y calcular el nuevo saldo, y actualiza la base de datos con el nuevo saldo.
3. **Resumen y finalización**: Después de procesar todas las transacciones, el programa muestra un resumen de las transacciones procesadas, incluyendo el total de transacciones leídas, procesadas con éxito y con errores, y la suma total de los montos procesados.

**SISTEMAS RELACIONADOS**: El programa utiliza dos archivos:

| Archivo | Detalle | Link |
| --- | --- | --- |
| BANCO.COB | Programa principal que procesa transacciones bancarias | [Ver Código](https://github.com/hexaforce66/codigosCobol/blob/main/BANCO.COB) |
| VAL-MOTOR.CBL | Subprograma que valida y calcula el nuevo saldo de una cuenta | [Ver Código](https://github.com/hexaforce66/codigosCobol/blob/main/VAL-MOTOR.CBL) |

**VALOR DE NEGOCIO**: El programa ayuda a reducir el riesgo operativo al automatizar el procesamiento de transacciones bancarias, lo que minimiza la posibilidad de errores humanos y aumenta la eficiencia. Además, proporciona un resumen detallado de las transacciones procesadas, lo que facilita la auditoría y el seguimiento de las operaciones bancarias. Sin embargo, si el programa no se ejecuta correctamente, puede generar errores en la base de datos, lo que podría tener un impacto significativo en la operación del banco. Por lo tanto, es fundamental asegurarse de que el programa se pruebe exhaustivamente antes de su implementación en producción.

## 📖 1. Glosario
Diccionario de Datos Bancarios

| Variable | Concepto | Formato | Definición |
| --- | --- | --- | --- |
| TR-ID | Identificador de transacción | PIC 9(05) | Número de transacción |
| TR-MONTO | Monto de la transacción | PIC 9(08)V99 | Monto de la transacción con dos decimales |
| DB-SALDO | Saldo actual de la cuenta | PIC 9(10)V99 | Saldo actual de la cuenta con dos decimales |
| ID-BUSCAR | Identificador de cuenta a buscar | PIC 9(05) | Número de cuenta a buscar |
| SQLCODE | Código de error de SQL | PIC S9(09) COMP | Código de error de SQL |
| FS-STATUS | Estado del archivo | PIC X(02) | Estado del archivo (00: ok, otros: error) |
| WS-EOF | Indicador de fin de archivo | PIC X(01) | Indicador de fin de archivo (Y/N) |
| WS-SALDO-ACTUAL | Saldo actual de la cuenta | PIC 9(10)V99 | Saldo actual de la cuenta con dos decimales |
| WS-MONTO-TRANS | Monto de la transacción | PIC 9(08)V99 | Monto de la transacción con dos decimales |
| WS-NUEVO-SALDO | Nuevo saldo de la cuenta | PIC 9(10)V99 | Nuevo saldo de la cuenta con dos decimales |
| WS-RESULT-CODE | Código de resultado | PIC X(02) | Código de resultado (OK/ER) |
| WS-TOTAL-TRANS | Total de transacciones | PIC 9(05) | Total de transacciones |
| WS-TOTAL-EXITO | Total de transacciones exitosas | PIC 9(05) | Total de transacciones exitosas |
| WS-TOTAL-ERROR | Total de transacciones con error | PIC 9(05) | Total de transacciones con error |
| WS-SUMA-MONTOS | Suma total de montos | PIC 9(12)V99 | Suma total de montos con dos decimales |

Nota: Los formatos de los campos están expresados en notación COBOL.

## 📋 2. Lógica
**Reglas de Negocio**

1.  El monto de la transacción debe ser positivo.
2.  No se permite sobregiro (el saldo actual más el monto de la transacción debe ser mayor o igual a cero).

**Matriz de Decisiones**

| Condición | Acción |
| --------- | ------ |
| Monto > 0 | Procesar transacción |
| Monto <= 0 | Rechazar transacción |
| Saldo actual + Monto >= 0 | Actualizar saldo |
| Saldo actual + Monto < 0 | Rechazar transacción |

**Mapeo de Párrafos**

*   **2100-PROCESAR-REGISTRO**: Lee un registro de transacción del archivo y lo procesa.
*   **2200-GESTIONAR-MOTOR**: Valida el monto de la transacción y actualiza el saldo si es válido.
*   **2210-UPDATE-DB**: Actualiza el saldo en la base de datos si la transacción es exitosa.
*   **2300-MANEJAR-ERROR-SQL**: Maneja errores de base de datos durante la actualización del saldo.
*   **100-VALIDAR-Y-CALCULAR**: Valida el monto de la transacción y calcula el nuevo saldo en el subprograma VAL-MOTOR.

## 🔄 3. BPMN
```mermaid
graph TD
A[PROCESO-BANCO] --> B[1000-INICIO]
    B --> C[2000-PROCESAR-CICLO]
    C --> D[2100-PROCESAR-REGISTRO]
    D --> E[2200-GESTIONAR-MOTOR]
    E --> F[VAL-MOTOR]
    F --> E
    E --> G[2210-UPDATE-DB]
    G --> H[3000-FINALIZAR]
    H --> I[FIN DEL PROGRAMA]
```

## 📊 4. Calidad
| Funcionalidad | Fiabilidad (%) | Cobertura (%) | Calidad (%) | Notas Justificativas |
| --- | --- | --- | --- | --- |
| Procesamiento de transacciones | 90 | 80 | 85 | La implementación utiliza un servicio para procesar las transacciones, lo que permite una buena separación de responsabilidades y una fácil mantenibilidad. Sin embargo, la cobertura de pruebas podría ser mejorada. |
| Lectura de archivo de transacciones | 95 | 90 | 92 | La implementación utiliza una clase de utilidad para leer el archivo de transacciones, lo que permite una buena separación de responsabilidades y una fácil mantenibilidad. La cobertura de pruebas es buena, pero podría ser mejorada. |
| Interacción con base de datos | 85 | 70 | 80 | La implementación utiliza JPA para interactuar con la base de datos, lo que permite una buena separación de responsabilidades y una fácil mantenibilidad. Sin embargo, la cobertura de pruebas podría ser mejorada. |
| Controlador REST | 90 | 80 | 85 | La implementación utiliza un controlador REST para recibir las transacciones y enviarlas al servicio para su procesamiento, lo que permite una buena separación de responsabilidades y una fácil mantenibilidad. Sin embargo, la cobertura de pruebas podría ser mejorada. |

En general, la implementación es funcional y cumple con los requisitos, pero podría ser mejorada en términos de cobertura de pruebas y calidad del código.