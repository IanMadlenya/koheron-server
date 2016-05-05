# Generate the implementation template for the device
#
# (c) Koheron

import os
import device as dev_utils

def Generate(device, directory):
    filename = os.path.join(directory, device.class_name.lower() + '.cpp')
    f = open(filename, 'w')
        
    try:      
        PrintFileHeader(f, os.path.basename(filename))
        
        f.write('#include "' + device.class_name.lower() + '.hpp' + '"\n\n')
        
        f.write('#include "../core/commands.hpp"\n')
        f.write('#include "../core/kserver.hpp"\n')
        f.write('#include "../core/kserver_session.hpp"\n')
        #f.write('#include "../core/binary_parser.hpp"\n\n')
        
        f.write('namespace kserver {\n\n')
        
        f.write("#define THIS (static_cast<" + device.class_name + "*>(this))\n\n")
        
        for operation in device.operations:
            f.write('/////////////////////////////////////\n')
            f.write('// ' + operation["name"] + '\n\n')
            
            PrintParseArg(f, device, operation)
            PrintExecuteOp(f, device, operation)
        
        PrintIsFailed(f, device)
        PrintExecute(f, device)
           
        f.write('} // namespace kserver\n\n')
        
        f.close()
    except:
        f.close()
        os.remove(filename)
        raise
    
def PrintFileHeader(file_id, filename):
    file_id.write('/// ' + filename + '\n')
    file_id.write('///\n')
    file_id.write('/// Generated by devgen. \n')
    file_id.write('/// DO NOT EDIT. \n')
    file_id.write('///\n')
    file_id.write('/// (c) Koheron \n\n')
    
# -----------------------------------------------------------
# PrintParseArg:
# Autogenerate the parser
# -----------------------------------------------------------
    
def PrintParseArg(file_id, device, operation):
    file_id.write('template<>\n')
    file_id.write('template<>\n')
    
    file_id.write('int KDevice<' + device.class_name + ',' + device.name + '>::\n')
    file_id.write('        parse_arg<' + device.class_name + '::' \
                    + operation["name"] + '> (const Command& cmd,\n' )
    file_id.write('                KDevice<' + device.class_name + ',' \
                        + device.name + '>::\n')
    file_id.write('                Argument<' + device.class_name \
                    + '::' + operation["name"] + '>& args)\n' )
    file_id.write('{\n')
    
    try:
        PrintParserCore(file_id, device, operation)
    except TypeError:
        raise
        
    file_id.write('    return 0;\n')
    file_id.write('}\n\n')
    
def PrintParserCore(file_id, device, operation):
    arg_num = GetTotalArgNum(operation)
    
    if arg_num == 0:
        return

    file_id.write('    if (required_buffer_size<')
    for idx, arg in enumerate(operation["arguments"]):
        if idx < arg_num - 1:   
            file_id.write(arg["type"] + ',')
        else:
            file_id.write(arg["type"])
    file_id.write('>() != cmd.payload_size) {\n')
    file_id.write("        kserver->syslog.print(SysLog::ERROR, \"Invalid payload size\\n\");\n")
    file_id.write("        return -1;\n")
    file_id.write("    }\n\n")

    file_id.write('    auto args_tuple = parse_buffer<0, ')
    for idx, arg in enumerate(operation["arguments"]):
        if idx < arg_num - 1:   
            file_id.write(arg["type"] + ',')
        else:
            file_id.write(arg["type"])
    file_id.write('>(&cmd.buffer[0]);\n')

    for idx, arg in enumerate(operation["arguments"]):
        file_id.write('    args.' + arg["name"] + ' = ' + 'std::get<' + str(idx) + '>(args_tuple);\n');

    
    # #PrintArgNumTest(file_id, arg_num, device.class_name, operation)
    # file_id.write("    char tmp_str[2*KSERVER_READ_STR_LEN];\n\n")
    
    # file_id.write("    uint32_t i = 0;\n")
    # file_id.write("    uint32_t cnt = 0;\n")
    # file_id.write("    uint32_t param_num = 0;\n\n")
    
    # file_id.write("    while(1) {\n")
    # file_id.write("        if(cmd.buffer[i]=='\\0') {\n")
    # file_id.write("            break;\n")
    # file_id.write("        }\n")
    # file_id.write("        else if(cmd.buffer[i]=='|') {\n")
    # file_id.write("            tmp_str[cnt] = '\\0';\n\n")

    # file_id.write("            switch(param_num)\n")
    # file_id.write("            {\n")
    
    # for idx, arg in enumerate(operation["arguments"]):   
    #     if "flag" in arg and arg["flag"] == 'CLIENT_ONLY':
    #         continue
                    
    #     macro_name = GetConvMacro(arg["type"])
        
    #     if macro_name == 'Type error':
    #         raise TypeError('\nIn device ' + device.class_name + ':\n' \
    #                         + 'In operation ' + operation["name"] + ':\n' \
    #                         + 'Invalid type for "' + arg["name"] \
    #                                 + '" -> ' + arg["type"])
                                    
    #     file_id.write("              case " + str(idx) + ": {\n")
            
    #     if not "cast" in arg:
    #         file_id.write("                  args." + arg["name"] +\
    #                                  " = " + macro_name + "(tmp_str);\n")
    #     else:
    #         file_id.write("                  args." + arg["name"] +\
    #                                  " = static_cast<" + arg["cast"] + ">("\
    #                                      + macro_name + "(tmp_str));\n")
            
    #     file_id.write("                  break;\n")
    #     file_id.write("              }\n")
    
    # file_id.write("            }\n\n")
    
    # file_id.write("            param_num++;\n")
    # file_id.write("            cnt = 0;\n")
    # file_id.write("            i++;\n")
    # file_id.write("        } else {\n")
    # file_id.write("            tmp_str[cnt] = cmd.buffer[i];\n")
    # file_id.write("            i++;\n")
    # file_id.write("            cnt++;\n")
    # file_id.write("        }\n")
    # file_id.write("    }\n\n")
    
    # file_id.write("    if(param_num == 0 || param_num > " + str(arg_num) + ") {\n")
    # file_id.write("        kserver->syslog.print(SysLog::ERROR, \"Invalid number of parameters\\n\");\n")
    # file_id.write("        return -1;\n")
    # file_id.write("    }\n\n")
    
def GetTotalArgNum(operation):
    if not dev_utils.IsArgs(operation):
        return 0
            
    return len(operation["arguments"])
# -----------------------------------------------------------
# ExecuteOp
# -----------------------------------------------------------
    
def PrintExecuteOp(file_id, device, operation):
    file_id.write('template<>\n')
    file_id.write('template<>\n')
    
    file_id.write('int KDevice<' + device.class_name + ',' \
                                    + device.name + '>::\n')
    file_id.write('        execute_op<' + device.class_name + '::' \
                            + operation["name"] + '> \n' )
                    
    file_id.write('        (const Argument<' + device.class_name + '::' \
                            + operation["name"] + '>& args, SessID sess_id)\n')
    
    file_id.write('{\n')
    
    # Load code fragments
    for frag in device.frag_handler.fragments:
        if operation["name"] == frag['name']:        
            for line in frag['fragment']:
                file_id.write(line)
    
    file_id.write('}\n\n')
    
def PrintIsFailed(file_id, device):
    file_id.write('template<>\n')
    file_id.write('bool KDevice<' + device.class_name + ',' \
                    + device.name + '>::is_failed(void)\n')
    file_id.write('{\n')
    
    for frag in device.frag_handler.fragments:
        if frag['name'] == "IS_FAILED":        
            for line in frag['fragment']:
                file_id.write(line)
    
    file_id.write('}\n\n')
    
def PrintExecute(file_id, device):
    file_id.write('template<>\n')
    file_id.write('int KDevice<' + device.class_name \
                                + ',' + device.name + '>::\n')
    file_id.write('        execute(const Command& cmd)\n' )
    file_id.write('{\n')
    
    file_id.write('#if KSERVER_HAS_THREADS\n')
    file_id.write('    std::lock_guard<std::mutex> lock(THIS->mutex);\n')
    file_id.write('#endif\n\n')
    
    file_id.write('    switch(cmd.operation) {\n')
    
    for operation in device.operations:
        file_id.write('      case ' + device.class_name + '::' \
                                + operation["name"] + ': {\n')
        file_id.write('        Argument<' + device.class_name + '::' \
                                + operation["name"] + '> args;\n\n')
        file_id.write('        if (parse_arg<' + device.class_name + '::' \
                                + operation["name"] + '>(cmd, args) < 0)\n')
        file_id.write('            return -1;\n\n')
        file_id.write('        return execute_op<' + device.class_name + '::' \
                                + operation["name"] + '>(args, cmd.sess_id);\n')                                             
        file_id.write('      }\n')
        
    file_id.write('      case ' + device.class_name + '::' \
                                + device.name.lower() + '_op_num:\n')
    file_id.write('      default:\n')
    file_id.write('          kserver->syslog.print(SysLog::ERROR, "' 
                            + device.class_name + ': Unknown operation\\n");\n')
    file_id.write('          return -1;\n')
    
    file_id.write('    }\n')
    
    file_id.write('}\n\n')

