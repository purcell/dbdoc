REM
REM Author   : Andy Todd (andy47@halfcooked.com)
REM Date     : 5th November, 2001
REM Filename : create_tables.sql
REM Purpose;
REM Oracle Version of sample tables for dbdoc application (http://dbdoc.sf.net)
REM The tables are borrowed from an example application shipped with the
REM Enhydra application server.
REM

CREATE TABLE person
  ( 
    login           VARCHAR2(32) NOT NULL ,
    password        VARCHAR2(32) NOT NULL ,
    firstname       VARCHAR2(32) NOT NULL ,
    lastname        VARCHAR2(32) NOT NULL ,
    ObjectId        NUMBER(8,0)  CONSTRAINT person_pk PRIMARY KEY ,
    ObjectVersion   INTEGER      NOT NULL 
  );


CREATE TABLE disc
  (
    title           VARCHAR2(32) NOT NULL ,
    artist          VARCHAR2(32) NOT NULL ,
    genre           VARCHAR2(32) NOT NULL ,
    owner           NUMBER(8,0)  NOT NULL CONSTRAINT person_fk 
                                          REFERENCES person(ObjectId) ,
    isLiked         CHAR(1)      NOT NULL CONSTRAINT isLiked_ck 
                                          CHECK (isLiked in ('Y', 'N')) ,
    ObjectId        NUMBER(8,0)  CONSTRAINT disc_pk PRIMARY KEY ,
    ObjectVersion   INTEGER      NOT NULL
  );

CREATE SEQUENCE object_id START WITH 1;
