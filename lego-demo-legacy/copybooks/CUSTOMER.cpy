       01  CUSTOMER-RECORD.
           05 CUST-ID             PIC X(10).
           05 CUST-STATUS         PIC X(1).
              88 CUST-ACTIVE      VALUE 'A'.
              88 CUST-BLOCKED     VALUE 'B'.
              88 CUST-CLOSED      VALUE 'C'.
           05 CUST-KYC-FLAG       PIC X(1).
              88 KYC-VALID        VALUE 'Y'.
              88 KYC-MISSING      VALUE 'N'.
           05 CUST-RISK-SEGMENT   PIC X(1).
              88 RISK-LOW         VALUE 'L'.
              88 RISK-MEDIUM      VALUE 'M'.
              88 RISK-HIGH        VALUE 'H'.
