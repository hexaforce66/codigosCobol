       01  RETURN-AREA.
           05 RETURN-CODE         PIC X(4).
              88 RET-APPROVED     VALUE '0000'.
              88 RET-CUST-ERR     VALUE '1001'.
              88 RET-ACCT-ERR     VALUE '2001'.
              88 RET-BAL-ERR      VALUE '3001'.
              88 RET-RISK-ERR     VALUE '4001'.
              88 RET-REVIEW       VALUE '9001'.
           05 RETURN-MESSAGE      PIC X(80).
           05 RETURN-RISK-SCORE   PIC 9(3).
