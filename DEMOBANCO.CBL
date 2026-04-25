       IDENTIFICATION DIVISION.
       PROGRAM-ID. DEMOBANCO.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 NUMERO-TARJETA     PIC 9(16) VALUE ZEROS.
       01 CUENTA-BANCARIA    PIC 9(10) VALUE ZEROS.
       01 RFC-CLIENTE        PIC X(13) VALUE SPACES.
       01 MONTO-TRANSACCION  PIC 9(7)V99 VALUE ZEROS.
       01 LIMITE-DIARIO      PIC 9(7)V99 VALUE 10000.00.
       01 RESPUESTA          PIC X(50).

       PROCEDURE DIVISION.
       INICIO.
           DISPLAY "Introduce el número de tarjeta::"
           ACCEPT NUMERO-TARJETA
           DISPLAY "Introduce la cuenta bancaria:"
           ACCEPT CUENTA-BANCARIA
           DISPLAY "Introduce el RFC del cliente:"
           ACCEPT RFC-CLIENTE
           DISPLAY "Introduce el monto de la transacción:"
           ACCEPT MONTO-TRANSACCION

           IF MONTO-TRANSACCION > LIMITE-DIARIO
               MOVE "Transacción rechazada: excede límite diario" TO RESPUESTA
           ELSE
               MOVE "Transacción aprobada" TO RESPUESTA
           END-IF

           DISPLAY RESPUESTA
           STOP RUN.
