# f = open('file.txt')
# lines = f.readlines()
# print(lines)
# idx = 0
# num_of_rules = 0
# readlines_at_once = 2
# key='[rules'
# for line in lines:
#     if line.startswith('[rules:'):
#         idx = lines.index(line)
#         num_of_rules = int(line.strip().removesuffix(']').split(':')[1])
#         break

#
# readlines_till = idx+1+(num_of_rules*readlines_at_once)
# print(f"{idx}, {num_of_rules}, {readlines_at_once} {readlines_till}")
# for line in lines[idx+1:readlines_till]:
#     print(line)
# lines_to_read = lines[idx+1:num_of_rules*readlines_at_once]
# print(lines_to_read)

# x = (lines.index(line) for line in lines if line.startswith(key))
# print(list(x)[0])
# d='[rulesets:2]'
# print(d.removesuffix(']').split(':')[1])

x = [('29638',
{
  '226534': {
    'priority': 17,
    'rule_id': '226534',
    'action': 'block',
    'identities': [

    ],
    'destinations': {
      'category_ids': [
        '8',
        '17',
        '22',
        '28',
        '36',
        '39',
        '51',
        '193',
        '194'
      ]
    },
    'inherit_ruleset_id': 'True'
  }
}),
('29677',
{
  '226775': {
    'priority': 18,
    'rule_id': '226775',
    'action': 'allow',
    'identities': [

    ],
    'destinations': {
      'category_ids': [
        '8'
      ]
    },
    'inherit_ruleset_id': 'True'
  }
}),
('46970',
{
  '366468': {
    'priority': 19,
    'rule_id': '366468',
    'action': 'block',
    'identities': [
      '10.10.0.0/32'
    ],
    'destinations': {
      'category_ids': [
        '1',
        '111',
        '112',
        '113',
        '114',
        '115',
        '116',
        '117',
        '145',
        '15',
        '161',
        '164',
        '2',
        '26',
        '32',
        '33',
        '4',
        '40',
        '45',
        '47',
        '48',
        '5',
        '56',
        '57',
        '6',
        '7',
        '8',
        '85'
      ]
    },
    'inherit_ruleset_id': 'True'
  },
  'ruleset_identities': {
    '34.218.209.254/32': [
      '10.10.0.0/32'
    ]
  }
}),
('47277',
{
  '369668': {
    'priority': 20,
    'rule_id': '369668',
    'action': 'block',
    'identities': [

    ],
    'destinations': {
      'category_ids': [
        '113',
        '17',
        '193',
        '194',
        '22',
        '28',
        '36',
        '38',
        '39',
        '51'
      ]
    },
    'inherit_ruleset_id': 'True'
  },
  '369025': {
    'priority': 21,
    'rule_id': '369025',
    'action': 'block',
    'identities': [

    ],
    'destinations': {
      'category_ids': [
        '1',
        '111',
        '15',
        '161',
        '164',
        '24',
        '4',
        '40',
        '45'
      ]
    },
    'inherit_ruleset_id': 'True'
  }
}),
('47389',
{
  '370093': {
    'priority': 22,
    'rule_id': '370093',
    'action': 'block',
    'identities': [
      '192.168.103.0/24'
    ],
    'destinations': {
      'category_ids': [
        '1',
        '161',
        '18',
        '40',
        '45'
      ]
    },
    'inherit_ruleset_id': 'True'
  },
  'ruleset_identities': {
    '123.63.117.105/32': [
      '192.168.103.0/24',
      '192.168.104.0/24'
    ]
  },
  '370090': {
    'priority': 23,
    'rule_id': '370090',
    'action': 'block',
    'identities': [
      '192.168.104.0/24'
    ],
    'destinations': {
      'category_ids': [
        '114',
        '6'
      ]
    },
    'inherit_ruleset_id': 'True'
  }
}),
('47391',
{
  '370100': {
    'priority': 24,
    'rule_id': '370100',
    'action': 'warn',
    'identities': [

    ],
    'destinations': {
      'category_ids': [
        '44',
        '52'
      ]
    },
    'inherit_ruleset_id': 'True'
  },
  '370099': {
    'priority': 25,
    'rule_id': '370099',
    'action': 'block',
    'identities': [

    ],
    'destinations': {
      'category_ids': [
        '17',
        '193',
        '194',
        '22',
        '28',
        '36',
        '51'
      ]
    },
    'inherit_ruleset_id': 'True'
  }
}),
('52472',
{
  '426278': {
    'priority': 26,
    'rule_id': '426278',
    'action': 'block',
    'identities': [
      '192.168.103.0/24'
    ],
    'destinations': {
      'category_ids': [
        '161',
        '27',
        '40',
        '45'
      ]
    },
    'inherit_ruleset_id': 'True'
  },
  'ruleset_identities': {
    '123.63.117.105/32': [
      '192.168.103.0/24',
      '192.168.104.0/24'
    ]
  },
  '422256': {
    'priority': 27,
    'rule_id': '422256',
    'action': 'block',
    'identities': [
      '192.168.104.0/24'
    ],
    'destinations': {
      'category_ids': [
        '17',
        '194',
        '24',
        '28',
        '39'
      ]
    },
    'inherit_ruleset_id': 'True'
  }
}),
('53307',
{
  '425501': {
    'priority': 28,
    'rule_id': '425501',
    'action': 'block',
    'identities': [
      '192.168.104.0/24'
    ],
    'destinations': {
      'category_ids': [
        '161',
        '40',
        '45'
      ]
    },
    'inherit_ruleset_id': 'True'
  },
  'ruleset_identities': {
    '123.63.117.105/32': [
      '192.168.103.0/24',
      '192.168.104.0/24'
    ]
  }
})]

d = {1:2}
d1={3:4}
d.update(d1)
print(d)
n_map = {'580008718': '18.118.37.124/32'}
s_map = {'58050604':{'18.118.37.124/32':'10.1.32.96/27','18.118.37.125/32':'10.1.32.97/27' }}
nw_map = {'18.118.37.124/32': ['10.10.11.0/32','10.10.11.0/32','172..31.3.174/32']}
nw = '58050604'
# if nw in s_map.keys():
#     nw = s_map[nw.values()]
print(str(s_map['58050604'].values()).split("[")[1].split("]")[0])
print(list(s_map['58050604'].keys())[0])
fv = {}
fv.update({1:{2:3}})
print(fv)
fv[1].update({4:5})
print(fv.keys())