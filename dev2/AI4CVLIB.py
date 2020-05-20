import sys
import os
import re
import string
from collections import Counter
import xml.etree.ElementTree as ET
import gensim
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS


SEARCH_RESULT_PATH = './search_result'
PROCESSED_DATA_PATH = './processed_data'

TABLE_NAME = 'feature_value_demo'

### 基本通用 ###

def clear_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
        

def load_file(file):
    with open(file) as f:  
        txt = f.read()
        return txt
    

def save_file(file,a_list):
    with open(file, 'w') as f:
        for line in a_list:
            f.write("%s\n" % line)
    print('Data is saved in '+ file)
    

def load_all_docs(dir_path):
	all_contents = []
	for file in os.listdir(dir_path):
		file_path = os.path.join(dir_path, file)
		if os.path.isfile(file_path):
			content = load_file(file_path)
			all_contents.append(content)
		else:
			print(file_path + ' does not exist.')
	return all_contents


### 本專案通用 ###

def load_query_tokens(file_path):
	if file_path == '':
		file_path = PROCESSED_DATA_PATH + '/tokens.txt'
	lines = []
	with open(file_path,'r') as f:
		for line in f.readlines():
			line = line.strip()
			if len(line) > 0:
				lines.append(line.lower())
	return lines


### nctid

def extract_id_from_file(file,drug):
    tree = ET.parse(file)
    root = tree.getroot()
    
    i = root.find('id_info')
    nct_id = i.find('nct_id')
    
    if drug:
        e = root.findall('intervention')
        for intervention in e:
            intervention_type = intervention.find('intervention_type').text
            if intervention_type == 'Drug':
                return nct_id.text
    
    return nct_id.text


def extract_all_ids(dataset_path = SEARCH_RESULT_PATH, processed_path = PROCESSED_DATA_PATH):
    all_ids = []
    
    for file in os.listdir(dataset_path):
        file_path = os.path.join(dataset_path, file)
        if os.path.isfile(file_path):
            nct_id = extract_id_from_file(file_path,False)
            if nct_id:
                all_ids.append(nct_id)
        else:
            print(file_path + ' does not exist.')
    
    all_ids.sort()
    
    with open(processed_path + '/all_ids.txt', 'w') as f:
        for line in all_ids:
            f.write("%s\n" % line)
    print('Data is saved in all_ids.txt.')


def load_all_ids(file_path):
    if file_path == "":
        file_path = PROCESSED_DATA_PATH+'/all_ids.txt'
    with open(file_path,'r') as f:
        lines = []
        for line in f.readlines():
            line = line.strip()
            lines.append(line)
        return lines


### criteria

def extract_criteria_from_file(file):
    tree = ET.parse(file)
    root = tree.getroot()
    
    e = root.find('eligibility')
    c = e.find('criteria')
    t = c.find('textblock')
    return (t.text.lower())


def extract_all_criteria(dataset_path = SEARCH_RESULT_PATH, processed_path = PROCESSED_DATA_PATH):
    all_ids = load_all_ids(processed_path+'/all_ids.txt')
    all_contents = []
    
    for the_id in all_ids:
        the_id = the_id.strip()
        file = the_id + '.xml'    
        file_path = os.path.join(dataset_path, file)
        if os.path.isfile(file_path):
            criteria = extract_criteria_from_file(file_path)
            content = ''
            content += the_id + '\n'
            content += criteria + '\n\n'
            all_contents.append(content)
        else:
            print(file_path + ' does not exist.')

    with open(processed_path + '/all_criteria.txt', 'w') as f:
        for lines in all_contents:
            f.write("%s\n" % lines)
    print('Data is saved in all_criteria.txt');


def extract_criteria_one_by_one(dataset_path = SEARCH_RESULT_PATH, processed_path = PROCESSED_DATA_PATH, saved_path = './criteria'):
    clear_folder(saved_path)
    
    all_ids = load_all_ids(processed_path+'/all_ids.txt')
    all_contents = []
    
    for the_id in all_ids:
        the_id = the_id.strip()
        file = the_id + '.xml'    
        file_path = os.path.join(dataset_path, file)
        if os.path.isfile(file_path):
            criteria = extract_criteria_from_file(file_path)
            content = ''
            content += the_id + '\n'
            content += criteria + '\n\n'
            all_contents.append(content)
            with open(saved_path+'/'+the_id+'.txt', 'w') as f:
                f.write("%s\n" % content)
        else:
            print(file_path + ' does not exist.')
  

def get_criteria_by_id(nct_id):
    dataset_path = './criteria'
    file1 = nct_id + '.inc'
    file2 = nct_id + '.exc'
    file_path_1 = os.path.join(dataset_path,file1)
    file_path_2 = os.path.join(dataset_path,file2)
    inc_cri = load_file(file_path_1).replace('(','').replace(')','').lower()
    exc_cri = load_file(file_path_2).replace('(','').replace(')','').lower()
    content = (inc_cri.lower(),exc_cri.lower())
    return content


def get_source_criteria_by_id(the_id):
    dataset_path = './search_result'
    file = the_id + '.xml'    
    file_path = os.path.join(dataset_path, file)
    if os.path.isfile(file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()    
        e = root.find('eligibility')
        c = e.find('criteria')
        t = c.find('textblock')
        return t.text


### treatments

def get_source_treatment_by_id(the_id):
    dataset_path = './search_result'
    file = the_id + '.xml'    
    file_path = os.path.join(dataset_path, file)
    if os.path.isfile(file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()    
        e = root.findall('intervention')
        intervention_txt = ''
        for intervention in e:
            intervention_name = intervention.find('intervention_name').text
            intervention_txt += intervention_name + '\n'
        return intervention_txt


### 抽取規則

def extract_operator(token,_string):
	token = token.replace('-',' ').lower()
	token = ' ' + token + ' '
	t_idx = _string.find(token)

	if re.search('≥|>=|>/=|',_string[t_idx+len(token):]):
		return '>='
	elif re.search('≤|<=|</=',_string[t_idx+len(token):]):
		return '<='
	elif re.search('>',_string[t_idx+len(token):]):
		return '>'
	elif re.search('<',_string[t_idx+len(token):]):
		return '<'
	elif re.search('=',_string[t_idx+len(token):]):
		return '='	
	else:
		return False


def extract_numberic_value(token,_string):
    token = token.replace('-',' ').lower()
    token = ' ' + token + ' '
    t_idx = _string.find(token)
        
    res = re.search('\d+',_string[t_idx+len(token):])
    if res:
        return res.group() 
    else :
        return False


def check_string_has_token(token,_string):
    ### 沒有用分詞套件的原因是，單一字元會被吃掉
    
    token = token.replace('-',' ').lower()
    token = ' ' + token + ' '

    for c in string.punctuation:
        _string = _string.replace(c,' ')
    # 處理邊界問題
    _string = ' ' + _string.lower() + ' '
    
    idx = _string.find(token)
    #sub = txt[idx:idx+len(token)+50]
    
    if idx == -1:
        return False
    else:
        return True


def check_criteria_start_line(line):
	res = re.match(r' {11}(-|[0-9]\.) ',line)
	if res != None:
		return True
	else:
		return False
		

def split_criteria(criteria_block):
	complete_line_list = []
	complete_line = ''

	lines = criteria_block.split('\n')
	for line in lines:
		line = line.strip()
		if len(line) > 0:
			complete_line += ' ' + line
		else:
			complete_line_list.append(complete_line)
			complete_line = ''
	return complete_line_list


def extract_feature_string(token,criteria_block):
	complete_line_list = split_criteria(criteria_block)
	for complete_line in complete_line_list:
		flag = check_string_has_token(token,complete_line)
		if flag:
			return complete_line
	return False

    
def extract_rule(token,criteria_block):
    rule = {}
    
    _string = extract_feature_string(token,criteria_block)
    if _string != False:
        numberic_value = extract_numberic_value(token,_string)
        operator = extract_operator(token,_string)
        if numberic_value == False:
            numberic_value = 0
        if operator == False:
            operator = '?'
            
        rule['string'] = _string
        rule['feature'] = token
        rule['operator'] = operator
        rule['value'] = numberic_value
        return rule
    return False


def extract_rules_from_criteria_file(token):
    rules_list = []
    all_ids = load_all_ids('./processed_data/all_ids.txt')
    dataset_path = './criteria'
    for _id in all_ids:
        inc_file = dataset_path + '/' + _id + '.inc'
        exc_file = dataset_path + '/' + _id + '.exc'
        inc_criteria = load_file(inc_file)
        exc_criteria = load_file(exc_file) 
        inc_rule = extract_rule(token,inc_criteria)
        exc_rule = extract_rule(token,exc_criteria)
        if inc_rule != False:
            inc_rule['nctid'] = _id
            inc_rule['feature'] = inc_rule['feature'].replace(' ','_') 
            inc_rule['criteria_type'] = 'inc'
            rules_list.append(inc_rule)
        if exc_rule != False:   
            exc_rule['nctid'] = _id
            exc_rule['criteria_type'] = 'exc'
            rules_list.append(exc_rule)
    return rules_list


def convert_to_sql(r):
    sql = 'INSERT INTO `' + TABLE_NAME + '`(`nctid`,`feature`,`operator`,`value`,`criteria_type`)VALUES("'+r['nctid']+'","'+r['feature']+'","'+r['operator']+'",'+str(r['value'])+',"'+r['criteria_type']+'");'
    return sql
    
 
     
    
    
         
            