-- 前提条件：
-- 1. alic_attribute,添加int类型字段list_id
--   alter table alic_attribute add list_id int(11) comment '选项列表ID';
-- 2. ali_category_attribute_datasource中的字段名alica_rid修改为list_id
--   alter table alica_datasource change alica_rid list_id int(11) comment '选项列表ID';

-- select count(*) from alica_datasource;

--只执行一次，初始化用

ALTER TABLE  `lytdb`.`tmp_table` 
 ADD  INDEX if not exists `listId`(`list_id`);
 

update  alic_attribute set list_id=alica_rid;

drop table if exists tmp_table;
create table tmp_table
as
select option_ids, min(list_id) as list_id, count(*) as cnt, group_concat(distinct attr_ids) as attr_ids, group_concat(distinct record_ids) as record_ids
from (
select l.list_id, count(*) as cnt, group_concat(l.value) as option_ids, group_concat(l.text) as texts, 
	group_concat(distinct a.name) as attr_ids, group_concat(distinct concat(',', a.alica_rid, ',')) as record_ids
from alica_datasource l, alic_attribute a
where l.list_id=a.alica_rid
group by l.list_id
order by 2 desc
) t
group by option_ids
order by 3 desc;

update alic_attribute a
inner join (select * from tmp_table where cnt>1) t
on t.record_ids like concat('%,', a.alica_rid, ',%')
set a.list_id=t.list_id;


alter table alica_datasource
drop foreign key if exists ali_category_attribute_datasource_ibfk_1;

-- 以下是删除 alica_datasource 中的多余数据（分开删除是性能原因）
delete from alica_datasource
where list_id in (select alica_rid from alic_attribute where alica_rid!=5 and list_id=5);

-- 以下SQL语句效率很低（可能需要10分钟以上），可使用delete join语句优化
delete from alica_datasource
where list_id not in (select distinct list_id from alic_attribute where ui_type!='input' and ui_type!='number');

-- select count(*) from alica_datasource;


-- 产生连续的选项ID，可直接作为静态列表的ID，从25900001开始
alter table alic_attribute
add if not exists new_list_id int(11) comment '选项列表ID（连续）';
alter table alica_datasource
add if not exists  new_list_id int(11) comment '选项列表ID（连续）';

-- update alic_attribute set new_list_id=null;
-- update alica_datasource set new_list_id=null;

update globaldb3.tmp_seqno set seq_no=25900001 where seq_name='productc_list_id';

update alic_attribute a
set new_list_id=globaldb3.get_next_seqno('productc_list_id')
where alica_rid=list_id and list_id in (select distinct list_id from alica_datasource);

update alica_datasource o
inner join (select distinct list_id, new_list_id from alic_attribute where alica_rid=list_id and new_list_id is not null) a
on o.list_id=a.list_id
set o.new_list_id=a.new_list_id;

update alic_attribute a
inner join (select * from alic_attribute where new_list_id is not null) b
on a.list_id=b.list_id and a.new_list_id is null and a.alica_rid!=b.alica_rid
set a.new_list_id=b.new_list_id;

-- 产生连续的选项ID，可直接作为元数据表的ID，从99100001开始
alter table alic_attribute
add if not exists new_display_id int(11) comment '元数据表ID（连续）';

update globaldb3.tmp_seqno set seq_no=99100001 where seq_name='productc_display_field_id';

update alic_attribute 
set new_display_id=globaldb3.get_next_seqno('productc_display_field_id');


-- 产生连续的类型ID，可直接作为产品类型的ID，从52900001开始
alter table ali_category
add if not exists new_category_id int(11) comment '产品类型ID（连续）';

update globaldb3.tmp_seqno set seq_no=52900001 where seq_name='product_category_id';

update ali_category 
set new_category_id=globaldb3.get_next_seqno('product_category_id'); 

-- 产品类型
UPDATE lytdb.ali_category  c LEFT JOIN lytdb.ali_category  p on p.id = c.parent_id
SET c.parent_id = p.new_category_id;
update lytdb.ali_category set path_value = null;

UPDATE lytdb.ali_category  c LEFT JOIN lytdb.ali_category  p on p.new_category_id = c.parent_id
SET c.path_value = if(c.parent_id is null, null ,if(p.path_value is null ,p.new_category_id,concat(p.path_value,',', p.new_category_id))) 
where c.path_value not like concat(',',p.path_value,',',p.new_category_id) or c.path_value is null;
UPDATE lytdb.ali_category  c LEFT JOIN lytdb.ali_category  p on p.new_category_id = c.parent_id
SET c.path_value = if(c.parent_id is null, null ,if(p.path_value is null ,p.new_category_id,concat(p.path_value,',', p.new_category_id))) 
where c.path_value not like concat(',',p.path_value,',',p.new_category_id) or c.path_value is null;
UPDATE lytdb.ali_category  c LEFT JOIN lytdb.ali_category  p on p.new_category_id = c.parent_id
SET c.path_value = if(c.parent_id is null, null ,if(p.path_value is null ,p.new_category_id,concat(p.path_value,',', p.new_category_id))) 
where c.path_value not like concat(',',p.path_value,',',p.new_category_id) or c.path_value is null;
UPDATE lytdb.ali_category  c LEFT JOIN lytdb.ali_category  p on p.new_category_id = c.parent_id
SET c.path_value = if(c.parent_id is null, null ,if(p.path_value is null ,p.new_category_id,concat(p.path_value,',', p.new_category_id))) 
where c.path_value not like concat(',',p.path_value,',',p.new_category_id) or c.path_value is null;
UPDATE lytdb.ali_category  set path_value = if(path_value is null, new_category_id, concat(path_value,',', new_category_id));