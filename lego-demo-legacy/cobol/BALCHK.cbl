       IDENTIFICATION DIVISION.
       PROGRAM-ID. BALCHK.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-DUMMY PIC X VALUE SPACE.
       LINKAGE SECTION.
       COPY PAYMENT.
       COPY ACCOUNT.
       COPY RETURN_CODES.

       PROCEDURE DIVISION USING PAYMENT-RECORD ACCOUNT-RECORD RETURN-AREA.
       VALIDATE-BALANCE.
           IF ACC-BLOCKED OR ACC-CLOSED
               MOVE '2001' TO RETURN-CODE
               MOVE 'Account is not open' TO RETURN-MESSAGE
               GOBACK
           END-IF

           IF PAY-CURRENCY NOT = ACC-CURRENCY
               MOVE '2001' TO RETURN-CODE
               MOVE 'Payment currency differs from account currency'
                   TO RETURN-MESSAGE
               GOBACK
           END-IF

           IF PAY-AMOUNT > ACC-DAILY-LIMIT
               MOVE '9001' TO RETURN-CODE
               MOVE 'Payment exceeds daily limit and requires review'
                   TO RETURN-MESSAGE
               GOBACK
           END-IF

           IF PAY-AMOUNT > ACC-BALANCE
               MOVE '3001' TO RETURN-CODE
               MOVE 'Insufficient funds' TO RETURN-MESSAGE
               GOBACK
           END-IF

           MOVE '0000' TO RETURN-CODE
           MOVE 'Balance validation approved' TO RETURN-MESSAGE
           GOBACK.
