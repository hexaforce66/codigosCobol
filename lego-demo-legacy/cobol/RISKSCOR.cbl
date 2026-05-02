       IDENTIFICATION DIVISION.
       PROGRAM-ID. RISKSCOR.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-BASE-SCORE           PIC 9(3) VALUE ZERO.
       01 WS-AMOUNT-SCORE         PIC 9(3) VALUE ZERO.
       LINKAGE SECTION.
       COPY PAYMENT.
       COPY CUSTOMER.
       COPY ACCOUNT.
       COPY RETURN_CODES.

       PROCEDURE DIVISION USING PAYMENT-RECORD CUSTOMER-RECORD
                                ACCOUNT-RECORD RETURN-AREA.
       CALCULATE-RISK.
           MOVE 10 TO WS-BASE-SCORE

           IF RISK-MEDIUM
               ADD 30 TO WS-BASE-SCORE
           END-IF

           IF RISK-HIGH
               ADD 60 TO WS-BASE-SCORE
           END-IF

           IF PAY-AMOUNT > 10000
               MOVE 30 TO WS-AMOUNT-SCORE
           ELSE
               IF PAY-AMOUNT > 5000
                   MOVE 15 TO WS-AMOUNT-SCORE
               ELSE
                   MOVE 5 TO WS-AMOUNT-SCORE
               END-IF
           END-IF

           COMPUTE RETURN-RISK-SCORE = WS-BASE-SCORE + WS-AMOUNT-SCORE

           IF RETURN-RISK-SCORE > 80
               MOVE '4001' TO RETURN-CODE
               MOVE 'Payment rejected by risk score' TO RETURN-MESSAGE
               GOBACK
           END-IF

           IF RETURN-RISK-SCORE > 60
               MOVE '9001' TO RETURN-CODE
               MOVE 'Payment requires manual risk review' TO RETURN-MESSAGE
               GOBACK
           END-IF

           MOVE '0000' TO RETURN-CODE
           MOVE 'Risk validation approved' TO RETURN-MESSAGE
           GOBACK.
