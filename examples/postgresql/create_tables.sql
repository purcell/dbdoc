create table person
(
    login VARCHAR(32) DEFAULT '' NOT NULL   ,
    password VARCHAR(32) DEFAULT '' NOT NULL   ,
    firstname VARCHAR(32) DEFAULT '' NOT NULL   ,
    lastname VARCHAR(32) DEFAULT '' NOT NULL   ,
    ObjectId INT8 NOT NULL PRIMARY KEY,
    ObjectVersion INTEGER NOT NULL
);

create table Disc
(
    title VARCHAR(32) DEFAULT '' NOT NULL   ,
    artist VARCHAR(32) DEFAULT '' NOT NULL   ,
    genre VARCHAR(32) DEFAULT '' NOT NULL   ,
    owner INT8  NOT NULL  REFERENCES person ( ObjectId ) ,
    isLiked BOOL  NOT NULL   ,
    ObjectId INT8 NOT NULL PRIMARY KEY,
    ObjectVersion INTEGER NOT NULL
);

create table objectid(
 next INT8 NOT NULL 
);
