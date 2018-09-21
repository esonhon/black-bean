class Commands:
    class __Commands:
        def __init__(self, arg):
            command_list=[]
            for cmd in arg:
                name = cmd["name"]
                path = "data/IR/"+name
                file = open(path,"rb")
                ir = file.read()
                file.close()
                command_list.append(
                    {
                        "name":name,
                        "sequence":ir
                    }
                )
            self.list = command_list

        def __str__(self):
            return repr(self) + " " + str(self.list)

        def __check(self, name):
            for cmd in self.list:
                if name == cmd["name"]:
                    return cmd
            return False

        def add(self, command_dict):
            try:
                name = command_dict["name"]
                if not self.__check(name):
                    self.list.append(command_dict)
                    return True
                else:
                    print("That command already exists")
                    return False
            except KeyError:
                print("Key error")
                return False

        def delete(self, command):
                cmd = self.__check(command["name"])
                if cmd:
                    self.list.remove(cmd)
                    print(self.list)
                else:
                    return {"error":"Not found"}

        def get(self, name):
            cmd = self.__check(name)
            print("Getting cmd: "+str(cmd))
            return cmd if cmd else None

        def get_all(self):
            command_list = self.list
            return list(map(lambda x: x["name"], command_list))

    instance = None

    def __init__(self, arg):
        if not Commands.instance:
            Commands.instance = Commands.__Commands(arg)
        else:
            Commands.instance.val = arg

    def __getattr__(self, name):
        return getattr(self.instance, name)
