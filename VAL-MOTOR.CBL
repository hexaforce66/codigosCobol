IDENTIFICATION DIVISION.
       PROGRAM-ID. VAL-MOTOR.
       DATA DIVISION.
       LINKAGE SECTION.
       01 LK-AREA.
          05 LK-SALDO-ACT   PIC 9(10)V99.
          05 LK-MONTO-TRA   PIC 9(08)V99.
          05 LK-NUEVO-SAL   PIC 9(10)V99.
          05 LK-CODE        PIC X(02).
       PROCEDURE DIVISION USING LK-AREA.
           IF LK-MONTO-TRA > 0
               COMPUTE LK-NUEVO-SAL = LK-SALDO-ACT + LK-MONTO-TRA
               MOVE 'OK' TO LK-CODE
           ELSE
               MOVE 'ER' TO LK-CODE
           END-IF.
           EXIT PROGRAM.
