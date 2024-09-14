import json
import os

from PyAissistant.PyChatBot.Chat import Message, Chat
from PyAissistant.PyChatBot.deep_seek_bot import DeepSeekBot

from ..obsolete_obsidian_utils import generate_uuid, obsidian_read_bot_response, obsidian_read_node, \
    obsidian_read_file, BOT_ROLE, USER_ROLE, get_relative_file_obsidian, flush_canvas_file, create_response_node, \
    create_node_chain


class InsChatBot(DeepSeekBot):

    def __init__(self, color_provider, file_title='-'):
        super().__init__(self.write_out_obsidian, function_call_feat=True)
        # options for obsidian assistant
        self.current_response_id = ''
        self.append_tool_call_result = True
        self.current_dir = None
        self.current_canvas_file = None
        self.current_node = None
        self.blink_node = None
        self.has_create_tool_call_node = False
        self.last_write_on = ''
        # options for chatbot
        self.title = file_title
        self.color_provider = color_provider
        self.default_prompt = ("As an AI chatbot in Obsidian, your job is to assist the user by generating responses "
                               "directly onto the canvas. Keep it straightforward, helpful, and organized.If there is "
                               "a complex task, finished it step by step.")

    def change_bot_name(self, new_bot_name) -> str:
        """
        change current bot name for system
        """
        self.title = new_bot_name
        return f'bot has change name to {new_bot_name}'

    def setup_function_tools(self):
        # super().setup_function_tools()
        # self.executor.extend_tools(list_exposed_functions())
        self.executor.add_tool(self.change_bot_name)
        pass

    def write_out_obsidian(self, word):
        target_file = self.last_write_on
        folder, _ = os.path.split(target_file)
        os.makedirs(folder, exist_ok=True)
        # there may be an IO exception.
        with open(target_file, 'a', encoding='utf-8') as flush_char_f:
            flush_char_f.write(word)
        print(word, end='')

    def get_current_append_file(self, create_type=''):
        canvas_folder, canvasName = os.path.split(self.current_canvas_file)
        return os.path.join(canvas_folder,
                            f'dialog/{canvasName}.ai.assets',
                            self.current_response_id,
                            f'{self.title}{create_type}.md')

    def get_response_id_from_line(self, line):
        if not line:
            return generate_uuid(32)
        try:
            first_line = line[len(self.block_mark) + 1:]
            json_data = json.loads(first_line)
            return json_data.get('id')
        except:
            return generate_uuid(32)

    def context_to_message(self, block):
        """
        obsidian node , create message object for bot completion
         - Message
         - BotMessage
         - ToolCall
         - ToolCallResult
        """
        block_id = block['id']
        if block_id.startswith(BOT_ROLE) or block['type'] == 'file':
            response_file = block['file']
            message = obsidian_read_bot_response(response_file, self.current_dir)
            return Message(message, BOT_ROLE)
        else:
            message = block['text']
            return Message(message, USER_ROLE)

    def complete_chat_to_pya_message(self, node_chain):
        system_nodes = [node for node in node_chain if self.is_node_flag(node, 'system')]
        file_ref_nodes = [node for node in node_chain if self.is_node_flag(node, 'file')]
        other_nodes = [node for node in node_chain if node not in system_nodes and node not in file_ref_nodes]
        print(f'Chain: message nodes:{len(other_nodes)}, '
              f'\nsys nodes:{len(system_nodes)} , '
              f'\nf nodes {len(file_ref_nodes)}'
              f'\ntotal {len(node_chain)}')
        system_prompt = ''
        reference_files = []
        if len(system_nodes) > 0:
            for node in system_nodes:
                txt, files = obsidian_read_node(node)
                if len(files) > 0:
                    reference_files.extend(files)
                system_prompt += f"{txt}\n"
            system_prompt = system_prompt.strip()
        if not system_prompt:
            system_prompt = self.default_prompt + ", Now you are play with Assistant named " + self.title
        if len(file_ref_nodes) > 0:
            for node in file_ref_nodes:
                _, files = obsidian_read_node(node)
                if len(files) > 0:
                    reference_files.extend(files)
        # remove duplicate files
        unique_files = list(set(reference_files))
        if len(unique_files) > 0:
            system_prompt += f"\n\n{len(unique_files)} files attached:\n"
            system_prompt += ''.join([obsidian_read_file(file, self.current_dir) for file in unique_files])

        # update system prompt
        self.current_chat.system_prompt = system_prompt

        return [self.context_to_message(node) for node in other_nodes]
        # return [Message(system_prompt, SYS_ROLE), *external_message]

    @staticmethod
    def is_node_flag(node, flag):
        if node.get('id', '').startswith(f'{flag}'):
            return True
        if node['type'] == flag and not node.get('id', '').startswith(f'{BOT_ROLE}'):
            return True
        if node.get('text', '').startswith(f'{flag}:'):
            return True
        return False

    def execute_func(self, function_tool, **kwargs):
        tool_details = function_tool['function']
        function_name = tool_details['name']
        call_result_file = self.get_current_append_file(create_type='.call_result')
        folder, _ = os.path.split(call_result_file)
        os.makedirs(folder, exist_ok=True)

        # before calling function
        if not self.append_tool_call_result:
            self.write_out_obsidian(f"\n> Working on `{function_name}` pls wait...")

        # make function calls
        exec_result = super().execute_func(function_tool, **kwargs)

        # after function calls , write out call result to file.
        with open(call_result_file, 'a', encoding='utf-8') as call_result_f:
            call_result_f.write(f'-------------------------------------------\n')
            call_result_f.write(f'#### call:{function_name}\n')
            call_result_f.write(f'- input: {kwargs}\n')
            call_result_f.write(f'- output: {exec_result}\n')
            call_result_f.write(f'\n')

        if self.append_tool_call_result:
            # ensure link had create or not.
            if not self.has_create_tool_call_node:
                self.has_create_tool_call_node = True
                self.create_tool_call_node(call_result_file)
        else:
            relative_file = get_relative_file_obsidian(os.path.abspath(call_result_file),
                                                       os.path.abspath(self.current_dir))
            self.write_out_obsidian(f'\n> Done. [RES.]({relative_file}) \n\n')

        return exec_result

    def create_tool_call_node(self, file):
        """
        create a tool call node to link to response node
        """
        _call_n_id = f"toolcall_{self.current_response_id}"
        blank_node = self.blink_node
        ori_x = blank_node.get('x', 0)
        ori_y = blank_node.get('y', 0)
        new_wid = 400
        new_hei = 600
        padding = 20
        new_x = ori_x - new_wid - padding * 3
        new_y = ori_y
        print(f'tool call : {file}')
        _node = {
            "id": "group-" + _call_n_id,
            "x": new_x,
            "y": new_y,
            "width": new_wid + padding * 2,
            "height": new_hei + padding * 2,
            "color": "3",
            "type": "group",
            "label": f"calls-{self.current_response_id}"
        }
        _node2 = {
            "id": _call_n_id,
            "x": new_x + padding,
            "y": new_y + padding,
            "width": new_wid,
            "height": new_hei,
            "type": "file",
            "file": get_relative_file_obsidian(os.path.abspath(file), os.path.abspath(self.current_dir))
        }
        _u_n_id = self.current_node['id']
        _r_n_id = self.blink_node['id']
        _link_1 = {
            'id': f"user-side_{self.current_response_id}",
            'fromNode': _u_n_id,
            'toNode': _call_n_id,
            'fromSide': 'bottom',
            "color": "3",
            'toSide': 'top'
        }
        _link_2 = {
            'id': f"bot-side_{self.current_response_id}",
            'fromNode': _call_n_id,
            'toNode': _r_n_id,
            'fromSide': 'bottom',
            'toSide': 'top'
        }
        with open(self.current_canvas_file, 'r', encoding='utf-8') as f:
            json_dat = json.load(f)
            nodes = json_dat['nodes']
            edges = json_dat['edges']
        nodes.append(_node)
        nodes.append(_node2)
        edges.append(_link_1)
        edges.append(_link_2)
        flush_canvas_file(self.current_canvas_file, nodes, edges, False, "3")

    @staticmethod
    def __exec_ai(matched_func, function_name, **kwargs):
        if matched_func is not None:
            try:
                exec_result = matched_func(**kwargs)
                if exec_result is not None:
                    return exec_result
                else:
                    return f"Function {function_name} successfully executed, but no return value found."
            except Exception as e:
                return f"Function {function_name} fail executed,{e}"
        else:
            return None

    @staticmethod
    def __wash_edge_with(edge, _id, _new_id):
        if edge.get('fromNode', '') == _id:
            edge['fromNode'] = _new_id
        if edge.get('toNode', '') == _id:
            edge['toNode'] = _new_id
        return edge

    def complete_obsidian_chat(self, node_id, canvas_file, nodes, edges, wdir):
        """
        it means node on canvas file under wdir is a chat node,
        we need to complete the chat node by adding messages to it.
        """
        ns = [n for n in nodes if n['id'] == node_id]
        node = ns[0]
        self.has_create_tool_call_node = False
        self.current_dir = wdir
        self.current_canvas_file = canvas_file
        self.current_node = node
        self.current_response_id = self.get_response_id_from_line(None)

        # step 1 , update current node text
        b_id = node['id']
        if '_' not in b_id:
            _new_role_id = f"{USER_ROLE}_{b_id}"
            node['id'] = _new_role_id
            edges = [self.__wash_edge_with(e, b_id, _new_role_id) for e in edges]

        text = str(node['text']).strip().strip('\\')
        node['text'] = text
        y_user, user_color = self.color_provider('user_dialog')
        if y_user and user_color != '0':
            node['color'] = user_color

        # step 2 , create a wink node to link to response node
        self.last_write_on = self.get_current_append_file()
        rel_file = get_relative_file_obsidian(self.last_write_on, os.path.abspath(self.current_dir))
        _, color_str = self.color_provider('assistant_dialog')
        new_node, new_trans = create_response_node(node, rel_file, color_str)
        nodes.append(new_node)
        edges.append(new_trans)
        self.blink_node = new_node
        # step 3 flush
        y_system, system_color = self.color_provider('system_dialog')
        flush_canvas_file(canvas_file, nodes, edges, y_system, system_color)

        # read message chain from canvas file.
        self.current_chat = Chat()
        node_chain = create_node_chain(node, nodes, edges)
        self.current_chat.messages.extend(self.complete_chat_to_pya_message(node_chain))

        # step 4 , begin chat with bot
        self.chat(text)
        print(' [DONE]')

    def set_config(self, botName, model_path, temperature, top_p, max_length, prompt):
        if botName:
            self.title = botName
        if model_path:
            self.model = model_path
        if temperature:
            self.temperature = temperature
        if top_p:
            self.top_p = top_p
        if max_length:
            self.max_tokens = max_length
        if temperature:
            self.temperature = temperature
        if top_p:
            self.top_p = top_p
        if max_length:
            self.max_tokens = max_length
        if prompt:
            self.default_prompt = prompt
            # print("Prompt:" + '\033[32m' + prompt + '\033[0m')
        pass
