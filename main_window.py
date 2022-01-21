from __future__ import annotations

import pprint
import sys
import time
import traceback
from PySimpleGUI import PySimpleGUI as sg
from psgtray import SystemTray
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rpc_client import RpcClient


class RPCGui:

    def __init__(self, client: RpcClient):
        self.appname = "Discord RPC (Music Bot)"
        self.client = client
        self.config = self.client.config
        self.ready = False

        self.log = {
            "regular": [],
            "warning": [],
            "error": []
        }

        self.langs = self.client.langs

        self.rpc_started = False

        self.window = self.get_window()
        menu = ['', ['Abrir Janela', 'Fechar App']]
        self.tray = SystemTray(menu, single_click_events=True, window=self.window, tooltip=self.appname)
        self.tray.hide_icon()
        self.window_loop()


    def get_window(self):

        theme = self.config.get("theme", "Reddit")

        sg.change_look_and_feel(theme)

        tab_config = [
            [
                sg.Frame("", [
                    [sg.Text('Tema do app:'),
                     sg.Combo(sg.theme_list(), default_value=theme, auto_size_text=True, key='theme',
                              enable_events=True)],
                    [sg.Text('Idioma da presence:'),
                     sg.Combo(list(self.langs), default_value=self.config["language"], auto_size_text=True,
                              key='language', enable_events=True)],
                    [sg.Checkbox('Exibir o botão: ver/ouvir música/vídeo.', default=self.config["show_listen_button"],
                                 key='show_listen_button', enable_events=True)],
                    [sg.Checkbox('Exibir o botão: playlist (quando disponível).',
                                 default=self.config["show_playlist_button"], key='show_playlist_button',
                                 enable_events=True)],
                    [sg.Checkbox('Adicionar o ID da playlist na url do botão de ver/ouvir (Youtube).',
                                 default=self.config["playlist_refs"], key='playlist_refs', enable_events=True)],
                    [sg.Checkbox('Exibir miniatura da música (quando disponível).',
                                 default=self.config["show_thumbnail"], key='show_thumbnail', enable_events=True)],
                    [sg.Checkbox('Exibir detalhes do canal onde o player está ativo (quantidade de membros, nome do '
                                 'servidor e canal, etc).', default=self.config["show_guild_details"],
                                 key='show_guild_details', enable_events=True)],
                    [sg.Checkbox('Exibir botão de convite do bot (quando disponível).',
                                 default=self.config['bot_invite'], key='bot_invite', enable_events=True)],
                    [sg.Checkbox('Carregar presence em todas as instâncias do discord (Beta).',
                                 default=self.config['load_all_instances'], key='load_all_instances', enable_events=True)],
                ], expand_x=True, key="asset_tab"),
            ]
        ]

        tab_assets = [
            [
                sg.Frame("", [
                    [sg.Text("Logo princpal (idle/thumb desativada):")],
                    [sg.Text("Loop/Repetição:")],
                    [sg.InputText(default_text=self.config["assets"]["loop"], expand_x=True, key="asset_loop",
                                  enable_events=True)],
                    [sg.Text("Loop/Repetição Fila:")],
                    [sg.InputText(default_text=self.config["assets"]["loop_queue"], expand_x=True,
                                  key="asset_loop_queue", enable_events=True)],
                    [sg.Text("Pausa:")],
                    [sg.InputText(default_text=self.config["assets"]["pause"], expand_x=True, key="asset_pause",
                                  enable_events=True)],
                    [sg.Text("Stream/Transmissão:")],
                    [sg.InputText(default_text=self.config["assets"]["stream"], expand_x=True, key="asset_stream",
                                  enable_events=True)],
                ], expand_x=True)
            ],
        ]

        tab_urls = [
            [
                sg.Frame("", [
                    [sg.Listbox(values=self.config["urls"], size=(60, 13),expand_x=True, key="url_list",
                                enable_events=True)],
                    [sg.InputText(expand_x=True, key="url_text"),
                     sg.Button("Adicionar", key="btn_add_url", enable_events=True),
                     sg.Button("Editar", key="btn_edit_url", enable_events=True),
                     sg.Button("Remover", key="btn_remove_url", enable_events=True)]
                ], expand_x=True)
            ]
        ]

        tabLogs = [
            [
                sg.TabGroup(
                    [
                        [
                            sg.Tab('Logs', [
                                [
                                    sg.Frame("", [
                                        [sg.Multiline("\n".join(self.log['regular'][-7:]), background_color="Black",
                                                      text_color="Cyan", key=f"log_regular",
                                                      disabled=True, autoscroll=True, expand_x=True, size=(0, 6))]
                                    ], expand_x=True, background_color="Black", title_color="White")
                                ],
                            ]),
                            sg.Tab('Alertas', [
                                [
                                    sg.Frame("", [
                                        [sg.Multiline("\n".join(self.log['warning'][-7:]), background_color="Black",
                                                      text_color="Yellow", key="log_warning",
                                                      disabled=True, autoscroll=True, expand_x=True, size=(0, 6))]
                                    ], expand_x=True, background_color="Black", title_color="White")
                                ],
                            ]),
                            sg.Tab('Erros', [
                                [
                                    sg.Frame("", [
                                        [sg.Multiline("\n".join(self.log['error'][-7:]), background_color="Black",
                                                      text_color="Red", key="log_error",
                                                      disabled=True, autoscroll=True, expand_x=True, size=(0, 6))]
                                    ], expand_x=True, background_color="Black", title_color="White")
                                ],
                            ])
                        ]
                    ], expand_x=True
                )
            ]
        ]

        tabgroup = [
            [
                sg.TabGroup(
                    [
                        [
                            sg.Tab('Config', tab_config, element_justification='center'),
                            sg.Tab('Socket URL\'s', tab_urls),
                            sg.Tab('Assets', tab_assets, element_justification='center')
                        ]
                    ]
                ),
            ],
            [
                [tabLogs],
                [sg.Button("Iniciar Presence", font=('MS Sans Serif', 13, 'bold'), key="start_presence",
                           disabled=self.rpc_started), sg.Button("Parar Presence", key="stop_presence",
                                                                 disabled=not self.rpc_started,
                                                                 font=('MS Sans Serif', 13, 'bold')),
                 sg.Button("Limpar Log", font=('MS Sans Serif', 13, 'bold'), key="clear_log"),
                 sg.Button("Fechar", key="exit", font=('MS Sans Serif', 13, 'bold')),
                 sg.Button("Salvar Alterações", font=('MS Sans Serif', 13, 'bold'), key="save_changes", visible=False),]

            ]
        ]

        return sg.Window(self.appname, tabgroup, finalize=True, enable_close_attempted_event=True)

    def update_log(self, text, tooltip=False, log_type="regular", exception: Exception = None):
        if not self.ready:
            time.sleep(2)
        if exception:
            sg.popup_error(f'Ocorreu um erro!', exception, traceback.format_exc())
            log_type = "error"
        self.log[log_type].append(text)
        self.window[f'log_{log_type}'].update("\n".join(self.log[log_type][-7:]))
        if tooltip and self.tray.tray_icon.visible:
            self.tray.show_message()
        self.ready = True

    def window_loop(self):

        while True:

            event, values = self.window.read()

            if event in (sg.WIN_CLOSED, 'exit'):
                self.client.exit()
                break

            elif event == self.tray.key:

                if values[event] in ("Abrir Janela", sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED,
                                     sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED):
                    self.window.un_hide()
                    self.window.bring_to_front()
                    self.tray.hide_icon()

                elif values[event] == "Fechar App":
                    self.tray.hide_icon()
                    self.client.exit()
                    break

            elif event == sg.WIN_CLOSE_ATTEMPTED_EVENT:
                self.window.hide()
                self.tray.show_icon()
                self.tray.show_message(self.appname, 'Executando em segundo plano.')

            elif event == "theme":
                self.config[event] = values[event]
                self.update_data()
                self.window.close()
                self.window = self.get_window()
                self.tray.window = self.window

            elif event == "clear_log":
                for l in self.log:
                    self.log[l].clear()
                    self.update_log("", log_type=l)

            elif event == "url_list":
                try:
                    self.window["url_text"].update(values[event][0])
                except IndexError:
                    continue

            elif event == "btn_add_url":

                if not values["url_text"].startswith(("ws://", "wss:/")):
                    sg.popup_ok(f"Você não inseriu um link válido!\n\nExemplo: ws://aaa.bbb.com:80/ws")

                elif values["url_text"] in self.window['url_list'].Values:
                    sg.popup_ok(f"O link já está na lista!")

                else:
                    self.config["urls"].append(values['url_text'])
                    self.update_urls()

            elif event == "btn_edit_url":

                if not values["url_list"]:
                    sg.popup_ok(f"Selecione um link para editar!")

                elif not values["url_text"].startswith(("ws://", "wss://")):
                    sg.popup_ok(f"Você não inseriu um link válido!\n\nExemplo: ws://aaa.bbb.com:80/ws")

                elif values["url_text"] == values["url_list"][0]:
                    sg.popup_ok(f"Você deve modificar o link!")

                else:
                    self.config["urls"].remove(values["url_list"][0])
                    self.config["urls"].append(values["url_text"])
                    self.update_urls()

            elif event == "btn_remove_url":
                if not values["url_list"]:
                    sg.popup_ok(f"Selecione um link para remover!")
                    continue
                self.config["urls"].remove(values["url_list"][0])
                self.update_urls()

            elif event == "start_presence":

                if not self.config["urls"]:
                    sg.popup_ok(f"Você deve adicionar pelo menos um link WS antes de iniciar presence!")
                    continue
                self.client.gui = self
                try:
                    self.client.get_app_instances()
                except Exception as e:
                    self.update_log(repr(e), exception=e)
                    continue
                self.client.start_ws()
                self.rpc_started = True
                self.window['start_presence'].update(disabled=True)
                self.window["stop_presence"].update(disabled=False)

            elif event == "stop_presence":
                self.client.close_app_instances()
                self.client.exit()
                time.sleep(2)
                self.update_log("RPC Finalizado!\n-----", tooltip=True)
                self.window["stop_presence"].update(disabled=True)
                self.window['start_presence'].update(disabled=False)
                self.rpc_started = False

            elif event == "save_changes":
                self.update_data()

            elif event.startswith("asset_"):
                self.window["save_changes"].update(visible=True)

            elif event in self.config:
                self.config[event] = values[event]
                self.update_data()

            elif event in self.config["assets"]:
                self.config["assets"][event] = values[event]
                self.update_data()

        try:
            self.window.close()
        except:
            pass
        sys.exit(0)


    def update_urls(self):
        self.window['url_list'].update(values=self.config["urls"])
        self.window["url_text"].update("")
        self.update_data(process_rpc=False)


    def update_data(self, process_rpc=True):

        self.client.save_json("./config.json", self.config)

        self.window["save_changes"].update(visible=False)

        if not process_rpc:
            return

        for user_id, user_data in self.client.last_data.items():

            for bot_id, bot_data in user_data.items():

                try:
                    self.client.process_data(user_id, bot_id, bot_data, refresh_timestamp=False)
                except Exception as e:
                    self.update_log(repr(e), log_type="error")
