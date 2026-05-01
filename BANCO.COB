IDENTIFICATION DIVISION.
       PROGRAM-ID. PROCESO-BANCO.

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SPECIAL-NAMES.
           DECIMAL-POINT IS COMMA.

       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRANS-FILE ASSIGN TO "transacciones.txt"
           ORGANIZATION IS LINE SEQUENTIAL
           FILE STATUS IS FS-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  TRANS-FILE.
       01  TRANS-REG.
           05 TR-ID          PIC 9(05).
           05 TR-MONTO       PIC 9(08)V99.

       WORKING-STORAGE SECTION.
       EXEC SQL BEGIN DECLARE SECTION END-EXEC.
       01 DB-SALDO           PIC 9(10)V99.
       01 ID-BUSCAR          PIC 9(05).
       01 SQLCODE            PIC S9(09) COMP.
       EXEC SQL END DECLARE SECTION END-EXEC.

       01 FS-STATUS          PIC X(02).
       01 WS-EOF             PIC X(01) VALUE 'N'.
          88 FIN-ARCHIVO     VALUE 'Y'.

      *--- ESTRUCTURA DE COMUNICACION (DEPENDENCIA) ---
       01 WS-AREA-INTERCAMBIO.
          05 WS-SALDO-ACTUAL PIC 9(10)V99.
          05 WS-MONTO-TRANS  PIC 9(08)V99.
          05 WS-NUEVO-SALDO  PIC 9(10)V99.
          05 WS-RESULT-CODE  PIC X(02).

       01 WS-CONTADORES.
          05 WS-TOTAL-TRANS   PIC 9(05) VALUE ZERO.
          05 WS-TOTAL-EXITO   PIC 9(05) VALUE ZERO.
          05 WS-TOTAL-ERROR   PIC 9(05) VALUE ZERO.
          05 WS-SUMA-MONTOS   PIC 9(12)V99 VALUE ZERO.

       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM 1000-INICIO.
           IF FS-STATUS = "00"
               PERFORM 2000-PROCESAR-CICLO UNTIL FIN-ARCHIVO
           END-IF.
           PERFORM 3000-FINALIZAR.
           STOP RUN.

       2100-PROCESAR-REGISTRO.
           ADD 1 TO WS-TOTAL-TRANS.
           MOVE TR-ID TO ID-BUSCAR.
           
           EXEC SQL 
               SELECT SALDO INTO :DB-SALDO 
               FROM CUENTAS 
               WHERE ID = :ID-BUSCAR 
           END-EXEC.

           IF SQLCODE = 0
               PERFORM 2200-GESTIONAR-MOTOR
           ELSE
               PERFORM 2300-MANEJAR-ERROR-SQL
           END-IF.

       2200-GESTIONAR-MOTOR.
      * PREPARAR DATOS PARA EL SUBPROGRAMA
           MOVE DB-SALDO TO WS-SALDO-ACTUAL
           MOVE TR-MONTO TO WS-MONTO-TRANS
           
      * LLAMADA AL SUBPROGRAMA (DEPENDENCIA)
           CALL 'VAL-MOTOR' USING WS-AREA-INTERCAMBIO
           
           IF WS-RESULT-CODE = 'OK'
               MOVE WS-NUEVO-SALDO TO DB-SALDO
               PERFORM 2210-UPDATE-DB
           ELSE
               DISPLAY "  AVISO: MOTOR RECHAZO ID " TR-ID
               ADD 1 TO WS-TOTAL-ERROR
           END-IF.

       2210-UPDATE-DB.
           EXEC SQL 
               UPDATE CUENTAS SET SALDO = :DB-SALDO WHERE ID = :ID-BUSCAR 
           END-EXEC.
           IF SQLCODE = 0
               ADD 1 TO WS-TOTAL-EXITO
               ADD TR-MONTO TO WS-SUMA-MONTOS
               EXEC SQL COMMIT END-EXEC
           END-IF.           
           PERFORM 3000-FINALIZAR.
           STOP RUN.

       1000-INICIO.
           DISPLAY "--- INICIANDO PROCESAMIENTO BANCARIO ---".
           OPEN INPUT TRANS-FILE.
           IF FS-STATUS NOT = "00"
               DISPLAY "ERROR CRITICO AL ABRIR TRANSACCIONES.TXT"
           END-IF.
           
           * CONEXION INICIAL (SIMULADA O REAL SEGUN TU PRECOMPILADOR)
           DISPLAY "CONECTANDO A LA BASE DE DATOS...".
           EXEC SQL CONNECT TO 'BANCO_DB' END-EXEC.

       2000-PROCESAR-CICLO.
           READ TRANS-FILE 
               AT END 
                  SET FIN-ARCHIVO TO TRUE
               NOT AT END 
                  PERFORM 2100-PROCESAR-REGISTRO
           END-READ.

       2100-PROCESAR-REGISTRO.
           ADD 1 TO WS-TOTAL-TRANS.
           MOVE TR-ID TO ID-BUSCAR.
           
           DISPLAY "PROCESANDO ID: " TR-ID " MONTO: " TR-MONTO.
           
           * 1. CONSULTA DE SALDO ACTUAL
           MOVE 0 TO SQLCODE.
           EXEC SQL 
               SELECT SALDO INTO :DB-SALDO 
               FROM CUENTAS 
               WHERE ID = :ID-BUSCAR 
           END-EXEC.

           IF SQLCODE = 0
               PERFORM 2200-ACTUALIZAR-CUENTA
           ELSE
               PERFORM 2300-MANEJAR-ERROR-SQL
           END-IF.

       2200-ACTUALIZAR-CUENTA.
           * LOGICA DE NEGOCIO: VALIDAR QUE EL MONTO SEA POSITIVO
           IF TR-MONTO > 0
               * OPERACION MATEMATICA DE TU CODIGO ORIGINAL
               COMPUTE DB-SALDO = DB-SALDO + TR-MONTO
               
               * ACTUALIZAR EN BASE DE DATOS
               EXEC SQL 
                   UPDATE CUENTAS 
                   SET SALDO = :DB-SALDO 
                   WHERE ID = :ID-BUSCAR 
               END-EXEC
               
               IF SQLCODE = 0
                   ADD 1 TO WS-TOTAL-EXITO
                   ADD TR-MONTO TO WS-SUMA-MONTOS
                   DISPLAY "   ACTUALIZACION EXITOSA."
                   EXEC SQL COMMIT END-EXEC
               ELSE
                   DISPLAY "   ERROR AL ACTUALIZAR ID: " TR-ID
                   ADD 1 TO WS-TOTAL-ERROR
                   EXEC SQL ROLLBACK END-EXEC
               END-IF
           ELSE
               DISPLAY "   AVISO: MONTO INVALIDO (CERO O NEGATIVO)"
               ADD 1 TO WS-TOTAL-ERROR
           END-IF.

       2300-MANEJAR-ERROR-SQL.
           IF SQLCODE = 100
               DISPLAY "   ERROR: LA CUENTA " TR-ID " NO EXISTE EN DB."
           ELSE
               DISPLAY "   ERROR DE BASE DE DATOS. CODIGO: " SQLCODE
           END-IF.
           ADD 1 TO WS-TOTAL-ERROR.

       3000-FINALIZAR.
           DISPLAY " ".
           DISPLAY "----------------------------------------------".
           DISPLAY "RESUMEN FINAL DEL PROCESAMIENTO:".
           DISPLAY "----------------------------------------------".
           
           MOVE WS-SUMA-MONTOS TO WS-MONTO-EDIT.
           DISPLAY "TOTAL TRANSACCIONES LEIDAS : " WS-TOTAL-TRANS.
           DISPLAY "TOTAL PROCESADAS CON EXITO : " WS-TOTAL-EXITO.
           DISPLAY "TOTAL CON ERRORES          : " WS-TOTAL-ERROR.
           DISPLAY "SUMA TOTAL PROCESADA       : " WS-MONTO-EDIT.
           
           CLOSE TRANS-FILE.
           DISPLAY "----------------------------------------------".
           DISPLAY "ARCHIVO CERRADO. FIN DEL PROGRAMA.".
