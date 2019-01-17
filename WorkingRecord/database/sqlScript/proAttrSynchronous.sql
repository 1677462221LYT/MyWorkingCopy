delete from globaldb3.comm_cfg_language where (record_rid between 25900000 and 25999999) or (record_rid between 99100000 and 99199999);

delete from globaldb3.comm_cfg_list where record_id between 25900000 and 25999999;

delete from globaldb3.comm_display_field_primary where record_id between 99100000 and 99199999;

delete from globaldb3.comm_display_field_sub where record_id between 99100000 and 99199999;

delete from globaldb3.comm_directory where record_id between 52900000 and 52999999 and dir_type = 'product_category';

-- 静态列表
INSERT INTO globaldb3.comm_cfg_list ( `tenant_id`, `record_id`, `name`, `description`, `cfg_level_type`, `list_value`, `change_flags`, `default_value`, `create_time`, `update_time` ) SELECT
1,
cad.new_list_id,
cad.new_list_id,
cad.new_list_id,
'system',
GROUP_CONCAT( cad.value ),
'',
NULL,
now( ),
now( ) 
FROM
 lytdb.alica_datasource cad 
WHERE
	 cad.new_list_id IS NOT NULL 
GROUP BY
	cad.new_list_id;
	
-- 静态列表语言
INSERT INTO globaldb3.comm_cfg_language ( `tenant_id`, `field_name`, `record_rid`, `language_name`, `name`, `create_time`, `update_time` ) 
SELECT
1,
'list_static_valuename',
cad.new_list_id,
'zh-CN',
GROUP_CONCAT( cad.text ),
now( ),
now( ) 
FROM
 lytdb.alica_datasource cad 
WHERE
	 cad.new_list_id IS NOT NULL 
GROUP BY
	cad.new_list_id;
	
INSERT INTO globaldb3.comm_cfg_language ( `tenant_id`, `field_name`, `record_rid`, `language_name`, `name`, `create_time`, `update_time` ) 
SELECT
1,
'list_static_valuename',
cad.new_list_id,
'en',
GROUP_CONCAT( cad.text ),
now( ),
now( ) 
FROM
 lytdb.alica_datasource cad 
WHERE
	 cad.new_list_id IS NOT NULL 
GROUP BY
	cad.new_list_id;
	
	
-- 产品类型
INSERT INTO globaldb3.comm_directory ( `tenant_id`, `record_id`, `account_id`, `dir_type`, `name`, `edit_flag`, `parent_rid`, `dir_level`, `path_rids`, `second_level_rid`, `leaf_flag`, `create_time`, `update_time` )
select 
1,
new_category_id,
1,
'product_category',
cn_name,
0,
parent_id,
`level`,
path_value,
new_category_id,
is_leaf,
now(),
now()
from lytdb.ali_category;

-- 产品属性
-- 将没有选项的设置为文本框
update alic_attribute 
set ui_type = 'input'
where ui_type in ('select','combobox','sequentialCombobox','colorSelector','checkbox','sequentialCheckbox','superCheckbox' )
and new_list_id is null;

-- 先新增
INSERT INTO globaldb3.comm_display_field_primary (
	`tenant_id`,
	`record_id`,
	`displayg_rid`,
	`table_name`,
	`field_category`,
	`display_category`,
	`column_name`,
	`array_flag`,
	`align_flag`,
	`edit_default_flag`,
	`edit_hide_flag`,
	`edit_hint_flag`,
	`edit_required_flag`,
	`enable_flag`,
	`readonly_flag`,
	`column_num`,
	`column_order`,
	`subcolumn_flag`,
	`column_suborder`,
	`column_width`,
	`quick_edit_flag`,
	`list_category`,
	`list_info`,
	`depended_flag`,
	`depend_column`,
	`link_category`,
	`link_url`,
	`floating_flag`,
	`floating_component`,
	`floating_column`,
	`ext_info`,
	`num_precision`,
	`val_category`,
	`val_para`,
	`show_expression`,
	`list_order`,
	`list_width`,
	`orig_table_name`,
	`orig_column_name`,
	`orig_index`,
	`detail_category`,
	`productc_rid`,
	`create_time`,
	`update_time`,
	`required_expression`,
	`readonly_expression` 
)   SELECT
1,
new_display_id,
21098501,
'product_feature',
3,
CASE
		aca.ui_type 
		WHEN 'select' THEN
		3 
		WHEN 'combobox' THEN
		3 
		WHEN 'input' THEN
		1 
		WHEN 'sequentialCombobox' THEN
		7 
		WHEN 'number' THEN
		5 
		WHEN 'taoSirProp' THEN
		5 
		WHEN 'colorSelector' THEN
		7
		WHEN 'checkbox' THEN
		7 
		WHEN 'sequentialCheckbox' THEN
		7 
		WHEN 'multiText' THEN
		1
		WHEN 'rangeUnit' THEN
		5 
		WHEN 'superCheckbox' THEN
		7 end,
		concat('col',new_display_id),
		0,
		0,
		0,
		0,
		0,
		0,
		1,
		ifnull(aca.readonly,0),
		1,
		0,
		0,
		0,
		24,
		0,
		if(aca.new_list_id is null,0,1),
		aca.new_list_id,
		0,
		NULL,
		0,
		NULL,
		0,
		NULL,
		NULL,
		NULL,
		0,
		0,
		NULL,
		NULL,
		0,
		120,
		NULL,
		NULL,
		NULL,
		1,
		ac.new_category_id,
		now(),
		now(),
		NULL,
	NULL 
FROM
  lytdb.ali_category ac
	INNER JOIN  lytdb.alic_attribute aca ON ac.new_id = aca.alic_nid ;
	
	-- 元数据子表
	INSERT INTO globaldb3.comm_display_field_sub ( `tenant_id`, `record_id`, `default_value`, `hide_flag`, `required_flag`, `create_time`, `update_time`, `export_flag` )  SELECT
1,
new_display_id,
text,
0,
required,
now( ),
now( ),
0 
FROM
	lytdb.alic_attribute;
	
-- 元数据语言
INSERT INTO globaldb3.comm_cfg_language ( `tenant_id`, `field_name`, `record_rid`, `language_name`, `name`, `create_time`, `update_time` ) SELECT
	1,
	'display_field_name',
	new_display_id,
	'zh-CN',
	`label_zh-CN`,
	now( ),
	now( ) 
FROM
	lytdb.alic_attribute;
	INSERT INTO globaldb3.comm_cfg_language ( `tenant_id`, `field_name`, `record_rid`, `language_name`, `name`, `create_time`, `update_time` ) SELECT
	1,
	'display_field_name',
	new_display_id,
	'en',
	`label_en`,
	now( ),
	now( ) 
FROM
	lytdb.alic_attribute;