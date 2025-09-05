from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        html_content = """
        <!DOCTYPE html>
        <html lang="en"><head><meta charset="UTF-8"><title>SimpleBar in QWebEngine</title>
          <link rel="stylesheet" href="https://unpkg.com/simplebar@latest/dist/simplebar.css" />
          <style>
            .my-scroll-container { max-height:200px; border:1px solid #ccc; margin:16px; }
            .my-scroll-container .simplebar-track.simplebar-vertical {
              background: rgba(0, 0, 128, 0.1);
            }
            .my-scroll-container .simplebar-scrollbar:before {
              background-color: #2196F3;
              border-radius: 4px;
            }
            .my-scroll-container .simplebar-scrollbar:hover:before {
              background-color: #1976D2;
            }
            .my-scroll-container .simplebar-scrollbar {
              transition: none !important;
            }
            .my-scroll-container .simplebar-scrollbar:before {
              opacity: 1 !important;
            }
            .my-scroll-container .simplebar-scrollbar { width: 10px !important; }
            .shared-listview-0 {
                display: flex;
                flex-direction: column;
                padding: (0.0, 0.0, 0.0, 0.0);
                flex-grow: 1;
                flex-basis: 0;
                overflow-y: auto;
            }
          </style>
        </head><body>
          <h1>SimpleBar in PySide6</h1>
          <div id="scroll-area" class="my-scroll-container" data-simplebar>
            <div id="fw_id_4" class="shared-listview-0">
                        <div id="fw_id_5" class="shared-listtile-0  ">
                            <p id="fw_id_6" class="shared-text-0">Item #0</p>
                        </div>
                        <div id="fw_id_7" class="shared-listtile-0  ">
                            <p id="fw_id_8" class="shared-text-0">Item #1</p>
                        </div>
                        <div id="fw_id_9" class="shared-listtile-0  ">
                            <p id="fw_id_10" class="shared-text-0">Item #2</p>
                        </div>
                        <div id="fw_id_11" class="shared-listtile-0  ">
                            <p id="fw_id_12" class="shared-text-0">Item #3</p>
                        </div>
                        <div id="fw_id_13" class="shared-listtile-0  ">
                            <p id="fw_id_14" class="shared-text-0">Item #4</p>
                        </div>
                        <div id="fw_id_15" class="shared-listtile-0  ">
                            <p id="fw_id_16" class="shared-text-0">Item #5</p>
                        </div>
                        <div id="fw_id_17" class="shared-listtile-0  ">
                            <p id="fw_id_18" class="shared-text-0">Item #6</p>
                        </div>
                        <div id="fw_id_19" class="shared-listtile-0  ">
                            <p id="fw_id_20" class="shared-text-0">Item #7</p>
                        </div>
                        <div id="fw_id_21" class="shared-listtile-0  ">
                            <p id="fw_id_22" class="shared-text-0">Item #8</p>
                        </div>
                        <div id="fw_id_23" class="shared-listtile-0  ">
                            <p id="fw_id_24" class="shared-text-0">Item #9</p>
                        </div>
                        <div id="fw_id_25" class="shared-listtile-0  ">
                            <p id="fw_id_26" class="shared-text-0">Item #10</p>
                        </div>
                        <div id="fw_id_27" class="shared-listtile-0  ">
                            <p id="fw_id_28" class="shared-text-0">Item #11</p>
                        </div>
                        <div id="fw_id_29" class="shared-listtile-0  ">
                            <p id="fw_id_30" class="shared-text-0">Item #12</p>
                        </div>
                        <div id="fw_id_31" class="shared-listtile-0  ">
                            <p id="fw_id_32" class="shared-text-0">Item #13</p>
                        </div>
                        <div id="fw_id_33" class="shared-listtile-0  ">
                            <p id="fw_id_34" class="shared-text-0">Item #14</p>
                        </div>
                        <div id="fw_id_35" class="shared-listtile-0  ">
                            <p id="fw_id_36" class="shared-text-0">Item #15</p>
                        </div>
                        <div id="fw_id_37" class="shared-listtile-0  ">
                            <p id="fw_id_38" class="shared-text-0">Item #16</p>
                        </div>
                        <div id="fw_id_39" class="shared-listtile-0  ">
                            <p id="fw_id_40" class="shared-text-0">Item #17</p>
                        </div>
                        <div id="fw_id_41" class="shared-listtile-0  ">
                            <p id="fw_id_42" class="shared-text-0">Item #18</p>
                        </div>
                        <div id="fw_id_43" class="shared-listtile-0  ">
                            <p id="fw_id_44" class="shared-text-0">Item #19</p>
                        </div>
                        <div id="fw_id_45" class="shared-listtile-0  ">
                            <p id="fw_id_46" class="shared-text-0">Item #20</p>
                        </div>
                        <div id="fw_id_47" class="shared-listtile-0  ">
                            <p id="fw_id_48" class="shared-text-0">Item #21</p>
                        </div>
                        <div id="fw_id_49" class="shared-listtile-0  ">
                            <p id="fw_id_50" class="shared-text-0">Item #22</p>
                        </div>
                        <div id="fw_id_51" class="shared-listtile-0  ">
                            <p id="fw_id_52" class="shared-text-0">Item #23</p>
                        </div>
                        <div id="fw_id_53" class="shared-listtile-0  ">
                            <p id="fw_id_54" class="shared-text-0">Item #24</p>
                        </div>
                        <div id="fw_id_55" class="shared-listtile-0  ">
                            <p id="fw_id_56" class="shared-text-0">Item #25</p>
                        </div>
                        <div id="fw_id_57" class="shared-listtile-0  ">
                            <p id="fw_id_58" class="shared-text-0">Item #26</p>
                        </div>
                        <div id="fw_id_59" class="shared-listtile-0  ">
                            <p id="fw_id_60" class="shared-text-0">Item #27</p>
                        </div>
                        <div id="fw_id_61" class="shared-listtile-0  ">
                            <p id="fw_id_62" class="shared-text-0">Item #28</p>
                        </div>
                        <div id="fw_id_63" class="shared-listtile-0  ">
                            <p id="fw_id_64" class="shared-text-0">Item #29</p>
                        </div>
                        <div id="fw_id_65" class="shared-listtile-0  ">
                            <p id="fw_id_66" class="shared-text-0">Item #30</p>
                        </div>
                        <div id="fw_id_67" class="shared-listtile-0  ">
                            <p id="fw_id_68" class="shared-text-0">Item #31</p>
                        </div>
                        <div id="fw_id_69" class="shared-listtile-0  ">
                            <p id="fw_id_70" class="shared-text-0">Item #32</p>
                        </div>
                        <div id="fw_id_71" class="shared-listtile-0  ">
                            <p id="fw_id_72" class="shared-text-0">Item #33</p>
                        </div>
                        <div id="fw_id_73" class="shared-listtile-0  ">
                            <p id="fw_id_74" class="shared-text-0">Item #34</p>
                        </div>
                        <div id="fw_id_75" class="shared-listtile-0  ">
                            <p id="fw_id_76" class="shared-text-0">Item #35</p>
                        </div>
                        <div id="fw_id_77" class="shared-listtile-0  ">
                            <p id="fw_id_78" class="shared-text-0">Item #36</p>
                        </div>
                        <div id="fw_id_79" class="shared-listtile-0  ">
                            <p id="fw_id_80" class="shared-text-0">Item #37</p>
                        </div>
                        <div id="fw_id_81" class="shared-listtile-0  ">
                            <p id="fw_id_82" class="shared-text-0">Item #38</p>
                        </div>
                        <div id="fw_id_83" class="shared-listtile-0  ">
                            <p id="fw_id_84" class="shared-text-0">Item #39</p>
                        </div>
                        <div id="fw_id_85" class="shared-listtile-0  ">
                            <p id="fw_id_86" class="shared-text-0">Item #40</p>
                        </div>
                        <div id="fw_id_87" class="shared-listtile-0  ">
                            <p id="fw_id_88" class="shared-text-0">Item #41</p>
                        </div>
                        <div id="fw_id_89" class="shared-listtile-0  ">
                            <p id="fw_id_90" class="shared-text-0">Item #42</p>
                        </div>
                        <div id="fw_id_91" class="shared-listtile-0  ">
                            <p id="fw_id_92" class="shared-text-0">Item #43</p>
                        </div>
                        <div id="fw_id_93" class="shared-listtile-0  ">
                            <p id="fw_id_94" class="shared-text-0">Item #44</p>
                        </div>
                        <div id="fw_id_95" class="shared-listtile-0  ">
                            <p id="fw_id_96" class="shared-text-0">Item #45</p>
                        </div>
                        <div id="fw_id_97" class="shared-listtile-0  ">
                            <p id="fw_id_98" class="shared-text-0">Item #46</p>
                        </div>
                        <div id="fw_id_99" class="shared-listtile-0  ">
                            <p id="fw_id_100" class="shared-text-0">Item #47</p>
                        </div>
                        <div id="fw_id_101" class="shared-listtile-0  ">
                            <p id="fw_id_102" class="shared-text-0">Item #48</p>
                        </div>
                        <div id="fw_id_103" class="shared-listtile-0  ">
                            <p id="fw_id_104" class="shared-text-0">Item #49</p>
                        </div>
                        <div id="fw_id_105" class="shared-listtile-0  ">
                            <p id="fw_id_106" class="shared-text-0">Item #50</p>
                        </div>
                        <div id="fw_id_107" class="shared-listtile-0  ">
                            <p id="fw_id_108" class="shared-text-0">Item #51</p>
                        </div>
                        <div id="fw_id_109" class="shared-listtile-0  ">
                            <p id="fw_id_110" class="shared-text-0">Item #52</p>
                        </div>
                        <div id="fw_id_111" class="shared-listtile-0  ">
                            <p id="fw_id_112" class="shared-text-0">Item #53</p>
                        </div>
                        <div id="fw_id_113" class="shared-listtile-0  ">
                            <p id="fw_id_114" class="shared-text-0">Item #54</p>
                        </div>
                        <div id="fw_id_115" class="shared-listtile-0  ">
                            <p id="fw_id_116" class="shared-text-0">Item #55</p>
                        </div>
                        <div id="fw_id_117" class="shared-listtile-0  ">
                            <p id="fw_id_118" class="shared-text-0">Item #56</p>
                        </div>
                        <div id="fw_id_119" class="shared-listtile-0  ">
                            <p id="fw_id_120" class="shared-text-0">Item #57</p>
                        </div>
                        <div id="fw_id_121" class="shared-listtile-0  ">
                            <p id="fw_id_122" class="shared-text-0">Item #58</p>
                        </div>
                        <div id="fw_id_123" class="shared-listtile-0  ">
                            <p id="fw_id_124" class="shared-text-0">Item #59</p>
                        </div>
                        <div id="fw_id_125" class="shared-listtile-0  ">
                            <p id="fw_id_126" class="shared-text-0">Item #60</p>
                        </div>
                        <div id="fw_id_127" class="shared-listtile-0  ">
                            <p id="fw_id_128" class="shared-text-0">Item #61</p>
                        </div>
                        <div id="fw_id_129" class="shared-listtile-0  ">
                            <p id="fw_id_130" class="shared-text-0">Item #62</p>
                        </div>
                        <div id="fw_id_131" class="shared-listtile-0  ">
                            <p id="fw_id_132" class="shared-text-0">Item #63</p>
                        </div>
                        <div id="fw_id_133" class="shared-listtile-0  ">
                            <p id="fw_id_134" class="shared-text-0">Item #64</p>
                        </div>
                        <div id="fw_id_135" class="shared-listtile-0  ">
                            <p id="fw_id_136" class="shared-text-0">Item #65</p>
                        </div>
                        <div id="fw_id_137" class="shared-listtile-0  ">
                            <p id="fw_id_138" class="shared-text-0">Item #66</p>
                        </div>
                        <div id="fw_id_139" class="shared-listtile-0  ">
                            <p id="fw_id_140" class="shared-text-0">Item #67</p>
                        </div>
                        <div id="fw_id_141" class="shared-listtile-0  ">
                            <p id="fw_id_142" class="shared-text-0">Item #68</p>
                        </div>
                        <div id="fw_id_143" class="shared-listtile-0  ">
                            <p id="fw_id_144" class="shared-text-0">Item #69</p>
                        </div>
                        <div id="fw_id_145" class="shared-listtile-0  ">
                            <p id="fw_id_146" class="shared-text-0">Item #70</p>
                        </div>
                        <div id="fw_id_147" class="shared-listtile-0  ">
                            <p id="fw_id_148" class="shared-text-0">Item #71</p>
                        </div>
                        <div id="fw_id_149" class="shared-listtile-0  ">
                            <p id="fw_id_150" class="shared-text-0">Item #72</p>
                        </div>
                        <div id="fw_id_151" class="shared-listtile-0  ">
                            <p id="fw_id_152" class="shared-text-0">Item #73</p>
                        </div>
                        <div id="fw_id_153" class="shared-listtile-0  ">
                            <p id="fw_id_154" class="shared-text-0">Item #74</p>
                        </div>
                        <div id="fw_id_155" class="shared-listtile-0  ">
                            <p id="fw_id_156" class="shared-text-0">Item #75</p>
                        </div>
                        <div id="fw_id_157" class="shared-listtile-0  ">
                            <p id="fw_id_158" class="shared-text-0">Item #76</p>
                        </div>
                        <div id="fw_id_159" class="shared-listtile-0  ">
                            <p id="fw_id_160" class="shared-text-0">Item #77</p>
                        </div>
                        <div id="fw_id_161" class="shared-listtile-0  ">
                            <p id="fw_id_162" class="shared-text-0">Item #78</p>
                        </div>
                        <div id="fw_id_163" class="shared-listtile-0  ">
                            <p id="fw_id_164" class="shared-text-0">Item #79</p>
                        </div>
                        <div id="fw_id_165" class="shared-listtile-0  ">
                            <p id="fw_id_166" class="shared-text-0">Item #80</p>
                        </div>
                        <div id="fw_id_167" class="shared-listtile-0  ">
                            <p id="fw_id_168" class="shared-text-0">Item #81</p>
                        </div>
                        <div id="fw_id_169" class="shared-listtile-0  ">
                            <p id="fw_id_170" class="shared-text-0">Item #82</p>
                        </div>
                        <div id="fw_id_171" class="shared-listtile-0  ">
                            <p id="fw_id_172" class="shared-text-0">Item #83</p>
                        </div>
                        <div id="fw_id_173" class="shared-listtile-0  ">
                            <p id="fw_id_174" class="shared-text-0">Item #84</p>
                        </div>
                        <div id="fw_id_175" class="shared-listtile-0  ">
                            <p id="fw_id_176" class="shared-text-0">Item #85</p>
                        </div>
                        <div id="fw_id_177" class="shared-listtile-0  ">
                            <p id="fw_id_178" class="shared-text-0">Item #86</p>
                        </div>
                        <div id="fw_id_179" class="shared-listtile-0  ">
                            <p id="fw_id_180" class="shared-text-0">Item #87</p>
                        </div>
                        <div id="fw_id_181" class="shared-listtile-0  ">
                            <p id="fw_id_182" class="shared-text-0">Item #88</p>
                        </div>
                        <div id="fw_id_183" class="shared-listtile-0  ">
                            <p id="fw_id_184" class="shared-text-0">Item #89</p>
                        </div>
                        <div id="fw_id_185" class="shared-listtile-0  ">
                            <p id="fw_id_186" class="shared-text-0">Item #90</p>
                        </div>
                        <div id="fw_id_187" class="shared-listtile-0  ">
                            <p id="fw_id_188" class="shared-text-0">Item #91</p>
                        </div>
                        <div id="fw_id_189" class="shared-listtile-0  ">
                            <p id="fw_id_190" class="shared-text-0">Item #92</p>
                        </div>
                        <div id="fw_id_191" class="shared-listtile-0  ">
                            <p id="fw_id_192" class="shared-text-0">Item #93</p>
                        </div>
                        <div id="fw_id_193" class="shared-listtile-0  ">
                            <p id="fw_id_194" class="shared-text-0">Item #94</p>
                        </div>
                        <div id="fw_id_195" class="shared-listtile-0  ">
                            <p id="fw_id_196" class="shared-text-0">Item #95</p>
                        </div>
                        <div id="fw_id_197" class="shared-listtile-0  ">
                            <p id="fw_id_198" class="shared-text-0">Item #96</p>
                        </div>
                        <div id="fw_id_199" class="shared-listtile-0  ">
                            <p id="fw_id_200" class="shared-text-0">Item #97</p>
                        </div>
                        <div id="fw_id_201" class="shared-listtile-0  ">
                            <p id="fw_id_202" class="shared-text-0">Item #98</p>
                        </div>
                        <div id="fw_id_203" class="shared-listtile-0  ">
                            <p id="fw_id_204" class="shared-text-0">Item #99</p>
                        </div>
                    </div>
          </div>
          <script src="https://unpkg.com/simplebar@latest/dist/simplebar.min.js"></script>
          <script>
            new SimpleBar(document.getElementById('scroll-area'), {
              autoHide: false,
              scrollbarMinSize: 20
            });
          </script>
        </body></html>
        """
        self.web_view.setHtml(html_content)
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
