       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTVAL.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-DUMMY PIC X VALUE SPACE.
       LINKAGE SECTION.
       COPY PAYMENT.
       COPY CUSTOMER.
       COPY RETURN_CODES.

       PROCEDURE DIVISION USING PAYMENT-RECORD CUSTOMER-RECORD RETURN-AREA.
       VALIDATE-CUSTOMER.
           IF PAY-CUSTOMER-ID = SPACES
               MOVE '1001' TO RETURN-CODE
               MOVE 'Customer id is mandatory' TO RETURN-MESSAGE
               GOBACK
           END-IF

           IF CUST-BLOCKED OR CUST-CLOSED
               MOVE '1001' TO RETURN-CODE
               MOVE 'Customer is not active' TO RETURN-MESSAGE
               GOBACK
           END-IF

           IF KYC-MISSING
               MOVE '1001' TO RETURN-CODE
               MOVE 'Customer KYC is incomplete' TO RETURN-MESSAGE
               GOBACK
           END-IF

           MOVE '0000' TO RETURN-CODE
           MOVE 'Customer validation approved' TO RETURN-MESSAGE
           GOBACK.
