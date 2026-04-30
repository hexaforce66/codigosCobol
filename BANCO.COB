IDENTIFICATION DIVISION.
       PROGRAM-ID. PROCESO-BANCO.
       AUTHOR. GEMINI-AI.
      * ESTE CODIGO MANTIENE COMPATIBILIDAD CON:
      * 1. transacciones.txt (ID y MONTO)
      * 2. init_db.sql (Tabla CUENTAS con ID y SALDO)

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
      *--- VARIABLES PARA SQL ---
       EXEC SQL BEGIN DECLARE SECTION END-EXEC.
       01 DB-SALDO           PIC 9(10)V99.
       01 ID-BUSCAR          PIC 9(05).
       01 SQLCODE            PIC S9(09) COMP.
       EXEC SQL END DECLARE SECTION END-EXEC.

      *--- VARIABLES DE CONTROL DE ARCHIVOS ---
       01 FS-STATUS          PIC X(02).
       01 WS-EOF             PIC X(01) VALUE 'N'.
          88 FIN-ARCHIVO     VALUE 'Y'.

      *--- VARIABLES DE LOGICA DE NEGOCIO ---
       01 WS-CONTADORES.
          05 WS-TOTAL-TRANS   PIC 9(05) VALUE ZERO.
          05 WS-TOTAL-EXITO   PIC 9(05) VALUE ZERO.
          05 WS-TOTAL-ERROR   PIC 9(05) VALUE ZERO.
          05 WS-SUMA-MONTOS   PIC 9(12)V99 VALUE ZERO.

       01 WS-FORMATOS-SALIDA.
          05 WS-MONTO-EDIT    PIC ZZZ.ZZZ.ZZ9,99.
          05 WS-SALDO-EDIT    PIC ZZZ.ZZZ.ZZ9,99.

       01 WS-BANDERAS.
          05 WS-EXISTE-CUENTA PIC X(01).
          05 WS-SALDO-OK      PIC X(01).

       PROCEDURE DIVISION.
       MAIN-LOGIC.
           PERFORM 1000-INICIO.
           
           IF FS-STATUS = "00"
               PERFORM 2000-PROCESAR-CICLO UNTIL FIN-ARCHIVO
           ELSE
               DISPLAY "ERROR: NO SE PUDO ABRIR EL ARCHIVO STATUS: " 
                       FS-STATUS
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
