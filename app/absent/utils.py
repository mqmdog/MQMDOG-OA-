def get_responder(request): # 获取审批人
    user = request.user
    # 如果当前用户是部门领导且是董事会成员，也就是董事会的头头，没有审批者；是部门领导但不是董事会主席，那么哪个部门提交申请就由负责哪个部门的董事会领导审批
    if user.department.leader.uid == user.uid: #当前用户的uid等于外键引用的部门leader的uid
        """
         # 访问路径分解：
         user.department.leader.uid == user.uid

        # 分解步骤：
        1. user → OAUser实例
        2. user.department → 用户所在的部门 (OAdepartment实例)
        3. user.department.leader → 该部门的领导 (OAUser实例)
        4. user.department.leader.uid → 部门领导的uid (字符串)
        5. user.uid → 当前用户的uid (字符串)
        """
        if user.department.name == '董事会':
            responder = None  # 是董事会主席，没有审批者
        else:
            responder = user.department.manager  # 是部门领导但不是董事会主席，那么哪个部门提交申请就由负责哪个部门的董事会领导审批
    # 如果不是部门leader
    else:
        responder = user.department.leader  # 审批者为部门leader
    return responder