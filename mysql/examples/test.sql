# MySQL dump 6.0
#
# Host: localhost    Database: test
#--------------------------------------------------------
# Server version	3.22.24

#
# Table structure for table 'colors'
#
CREATE TABLE COLORS (
  	COLOR varchar(32) DEFAULT '' NOT NULL,
  	PRIME_COLOR enum('No','Yes') DEFAULT 'No' NOT NULL,
  	LAST_DATE timestamp(14) DEFAULT '' NOT NULL,
  	OPEN_DATE timestamp(14) DEFAULT '' NOT NULL,
  	PRIMARY KEY (COLOR),
  	KEY PRIME_COLOR (PRIME_COLOR),
	KEY LAST_DATE (LAST_DATE),
	KEY OPEN_DATE (OPEN_DATE)
);

#
# Dumping data for table 'colors'
#

INSERT INTO COLORS VALUES ('red','Yes',NOW(),NOW());
INSERT INTO COLORS VALUES ('blue','Yes',NOW(),NOW());
INSERT INTO COLORS VALUES ('green','Yes',NOW(),NOW());
INSERT INTO COLORS VALUES ('yellow','No',NOW(),NOW());
INSERT INTO COLORS VALUES ('orange','No',NOW(),NOW());
INSERT INTO COLORS VALUES ('purple','No',NOW(),NOW());
INSERT INTO COLORS VALUES ('cyan','No',NOW(),NOW());

#
# Table structure for table 'team'
#
CREATE TABLE TEAM (
  	MEMBER_ID int(11) DEFAULT '0' NOT NULL auto_increment,
  	FIRST_NAME varchar(32) DEFAULT '' NOT NULL,
  	LAST_NAME varchar(32) DEFAULT '' NOT NULL,
  	REMARK varchar(64) DEFAULT '' NOT NULL,
  	FAV_COLOR varchar(32) DEFAULT '' NOT NULL,
	LAST_DATE timestamp(14) DEFAULT '' NOT NULL,  
	OPEN_DATE timestamp(14) DEFAULT '' NOT NULL,
  	PRIMARY KEY (MEMBER_ID),
  	KEY FAV_COLOR (FAV_COLOR),
	KEY LAST_DATE (LAST_DATE),
	KEY OPEN_DATE (OPEN_DATE)
);

#
# Dumping data for table 'team'
#

INSERT INTO TEAM VALUES (1,'Brad','Stec','Techno Needy','aquamarine',NOW(),NOW());
INSERT INTO TEAM VALUES (2,'Nick','Borders','Meticulous Nick','blue',NOW(),NOW());
INSERT INTO TEAM VALUES (3,'Brittney','McChristy','Data Diva','blue',NOW(),NOW());
INSERT INTO TEAM VALUES (4,'Fuzzy','Logic','The Logic Bunny','cyan',NOW(),NOW());

