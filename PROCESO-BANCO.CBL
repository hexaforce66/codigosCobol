IDENTIFICATION DIVISION.
       PROGRAM-ID. PROCESO-BANCO.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRANS-FILE ASSIGN TO "transacciones.txt"
           ORGANIZATION IS LINE SEQUENTIAL
           FILE STATUS IS FS-STATUS.
       DATA DIVISION.
       FILE SECTION.
       FD  TRANS-FILE.
       01  TRANS-REG.
           05 TR-ID           PIC 9(05).
           05 TR-MONTO        PIC 9(08)V99.
       WORKING-STORAGE SECTION.
       01 FS-STATUS           PIC X(02).
       01 WS-EOF              PIC X(01) VALUE 'N'.
          88 FIN-ARCHIVO      VALUE 'Y'.
       01 WS-AREA-INTERCAMBIO.
          05 WS-SALDO-ACTUAL  PIC 9(10)V99.
          05 WS-MONTO-TRANS   PIC 9(08)V99.
          05 WS-NUEVO-SALDO   PIC 9(10)V99.
          05 WS-RESULT-CODE   PIC X(02).
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           OPEN INPUT TRANS-FILE.
           PERFORM 2000-PROCESAR UNTIL FIN-ARCHIVO.
           CLOSE TRANS-FILE.
           STOP RUN.

       2000-PROCESAR.
           READ TRANS-FILE AT END SET FIN-ARCHIVO TO TRUE
           NOT AT END
               *> Dependencia 1: Consulta de Saldo en DB
               CALL 'DB-CONSULT' USING TR-ID WS-SALDO-ACTUAL
               
               *> Dependencia 2: Validación de Motor de Reglas
               MOVE TR-MONTO TO WS-MONTO-TRANS
               CALL 'VAL-MOTOR' USING WS-AREA-INTERCAMBIO
               
               IF WS-RESULT-CODE = 'OK'
                   *> Dependencia 3: Persistencia de Actualización
                   CALL 'DB-UPDATE' USING TR-ID WS-NUEVO-SALDO
               ELSE
                   *> Dependencia 4: Log de Errores Bancarios
                   CALL 'LOG-ERROR' USING TR-ID WS-RESULT-CODE
               END-IF
           END-READ.
