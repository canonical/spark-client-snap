CREATE DATABASE IF NOT EXISTS sparkdb;
USE sparkdb;
CREATE TABLE IF NOT EXISTS sparkdb.testTable (number Int, word String);
INSERT INTO sparkdb.testTable VALUES (1, "foo"), (2, "bar"), (3, "grok");
SELECT CONCAT("Inserted Rows: ", COUNT(*)) FROM sparkdb.testTable;
EXIT;
