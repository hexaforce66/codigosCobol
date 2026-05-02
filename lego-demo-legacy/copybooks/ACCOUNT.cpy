       01  ACCOUNT-RECORD.
           05 ACC-ID              PIC X(12).
           05 ACC-CUSTOMER-ID     PIC X(10).
           05 ACC-STATUS          PIC X(1).
              88 ACC-OPEN         VALUE 'O'.
              88 ACC-BLOCKED      VALUE 'B'.
              88 ACC-CLOSED       VALUE 'C'.
           05 ACC-BALANCE         PIC 9(9)V99.
           05 ACC-DAILY-LIMIT     PIC 9(9)V99.
           05 ACC-CURRENCY        PIC X(3).
