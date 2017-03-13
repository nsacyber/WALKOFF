
def orderless_list_comapre(klass, list1, list2):
    klass.assertEqual(len(list1), len(list2))
    klass.assertEqual(set(list1), set(list2))