DROP TABLE IF EXISTS ranger_masterkey CASCADE;
DROP SEQUENCE IF EXISTS ranger_masterkey_seq;
CREATE SEQUENCE ranger_masterkey_seq;
CREATE TABLE ranger_masterkey(
id BIGINT DEFAULT nextval('ranger_masterkey_seq'::regclass),
create_time TIMESTAMP DEFAULT NULL NULL,
update_time TIMESTAMP DEFAULT NULL NULL,
added_by_id BIGINT DEFAULT NULL NULL,
upd_by_id BIGINT DEFAULT NULL NULL,
cipher VARCHAR(255) DEFAULT NULL NULL ,
bitlength INT DEFAULT NULL NULL,
masterkey VARCHAR(2048),
PRIMARY KEY (id)
);

DROP TABLE IF EXISTS ranger_keystore CASCADE;
DROP SEQUENCE IF EXISTS ranger_keystore_seq;
CREATE SEQUENCE ranger_keystore_seq;
CREATE TABLE ranger_keystore(
id BIGINT DEFAULT nextval('ranger_keystore_seq'::regclass),
create_time TIMESTAMP DEFAULT NULL NULL,
update_time TIMESTAMP DEFAULT NULL NULL,
added_by_id BIGINT DEFAULT NULL NULL,
upd_by_id BIGINT DEFAULT NULL NULL,
kms_alias VARCHAR(255) NOT NULL,
kms_createdDate BIGINT DEFAULT NULL NULL,
kms_cipher VARCHAR(255) DEFAULT NULL NULL,
kms_bitLength BIGINT DEFAULT NULL NULL,
kms_description VARCHAR(512) DEFAULT NULL NULL,
kms_version BIGINT DEFAULT NULL NULL,
kms_attributes VARCHAR(1024) DEFAULT NULL NULL,
kms_encoded VARCHAR(2048),
PRIMARY KEY (id)
);
