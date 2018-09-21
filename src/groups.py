
class Groups:
    class __Groups:
        def __init__(self, arg):
            self.list = arg

        def __check(self, group_name):
            for group in self.list:
                if group["name"] == group_name:
                    return group
            return None

        def create(self, group_name):
            group={}
            group["name"]=group_name
            group["commands"]=[]
            self.list.append(group)
            return group

        def delete(self, group_name):
            group = self.get(group_name)
            if group:
                self.list.remove(group)
                return True
            return False

        def add(self, group_name, command):
            group = self.get(group_name)
            for cmd in group["commands"]:
                if cmd == command:
                    return False
            group["commands"].append(command)
            return group

        def remove(self, group_name, command):
            group = self.get(group_name)
            try:
                group["commands"].remove(command)
                return group
            except Exception as e:
                return False

        def get(self, group_name):
            group = self.__check(group_name)
            return group

        def get_all(self):
            group_list = self.list
            return group_list


    instance = None

    def __init__(self, arg):
        if not Groups.instance:
            Groups.instance = Groups.__Groups(arg)
        else:
            Groups.instance.val = arg

    def __getattr__(self, name):
        return getattr(self.instance, name)
