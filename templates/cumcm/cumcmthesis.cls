%%
%% This is file `cumcmthesis.cls',
%% -----------------------------------
%% 基于 LaTeX工作室 nmmcm.cls v4 (2025/04/26) 改编
%% 适用于 全国大学生数学建模竞赛 (CUMCM) 论文排版
%%
\NeedsTeXFormat{LaTeX2e}[1999/12/01]
\ProvidesClass{cumcmthesis}
  [2025/04/26 v4 The Thesis Template Designed For CUMCM]
\typeout{The Thesis Template Designed For CUMCM (全国大学生数学建模竞赛)}
\RequirePackage{xkeyval}
\RequirePackage{etoolbox}
\define@boolkey{MCM}[MCM@opt@]{CTeX}[false]{}
\define@boolkey{MCM}[MCM@opt@]{titlepage}[true]{}
\define@boolkey{MCM}[MCM@opt@]{abstract}[true]{}
\define@boolkey{MCM}[MCM@opt@]{sheet}[true]{}
\define@boolkey{MCM}[MCM@opt@]{withoutpreface}[false]{}
\define@boolkey{MCM}[MCM@opt@]{titleinsheet}[false]{}
\define@boolkey{MCM}[MCM@opt@]{keywordsinsheet}[false]{}
\define@cmdkeys{MCM}[MCM@opt@]{tcn,problem}
\define@key{MCM}{tcn}[0000]{\gdef\MCM@opt@tcn{#1}}
\define@key{MCM}{problem}[A]{\gdef\MCM@opt@problem{#1}}
\setkeys{MCM}{tcn=0000,problem=B}

\define@key{cumcmthesis.cls}{tcn}[0000]{\gdef\MCM@opt@tcn{#1}}
\define@key{cumcmthesis.cls}{problem}[A]{\gdef\MCM@opt@problem{#1}}
\define@boolkey{cumcmthesis.cls}[MCM@opt@]{titlepage}{}
\define@boolkey{cumcmthesis.cls}[MCM@opt@]{abstract}{}
\define@boolkey{cumcmthesis.cls}[MCM@opt@]{sheet}{}
\define@boolkey{cumcmthesis.cls}[MCM@opt@]{titleinsheet}{}
\define@boolkey{cumcmthesis.cls}[MCM@opt@]{keywordsinsheet}{}
\MCM@opt@sheettrue
\MCM@opt@titlepagetrue
\MCM@opt@titleinsheetfalse
\MCM@opt@keywordsinsheetfalse
\MCM@opt@abstracttrue
\newcommand{\mcmsetup}[1]{\setkeys{MCM}{#1}}
\ProcessOptionsX\relax
\LoadClass[a4paper, zihao=-4]{ctexart}
\newcommand{\team}{队号\ \MCM@opt@tcn}
\RequirePackage{fancyhdr, fancybox}
\RequirePackage{ifthen}
\RequirePackage{lastpage}
\RequirePackage{listings}

\RequirePackage{CJKulem}
 \usepackage{times}

% =================================================================
% 字体字号定义
% =================================================================
\newcommand{\chuhao}{\fontsize{42bp}{\baselineskip}\selectfont}
\newcommand{\xiaochuhao}{\fontsize{36pt}{\baselineskip}\selectfont}
\newcommand{\yihao}{\fontsize{28pt}{\baselineskip}\selectfont}
\newcommand{\xiaoyi}{\fontsize{24pt}{\baselineskip}\selectfont}
\newcommand{\erhao}{\fontsize{21pt}{\baselineskip}\selectfont}
\newcommand{\xiaoerhao}{\fontsize{18pt}{\baselineskip}\selectfont}
\newcommand{\sanhao}{\fontsize{15.75pt}{\baselineskip}\selectfont}
\newcommand{\xiaosanhao}{\fontsize{15pt}{\baselineskip}\selectfont}
\newcommand{\sihao}{\fontsize{14pt}{\baselineskip}\selectfont}
\newcommand{\xiaosihao}{\fontsize{12pt}{\baselineskip}\selectfont}
\newcommand{\wuhao}{\fontsize{10.5pt}{\baselineskip}\selectfont}
\newcommand{\xiaowuhao}{\fontsize{9pt}{\baselineskip}\selectfont}
\newcommand{\liuhao}{\fontsize{7.875pt}{\baselineskip}\selectfont}
\newcommand{\qihao}{\fontsize{5.25pt}{\baselineskip}\selectfont}
\newcommand{\song}{\CJKfamily{song}}
\newcommand{\KAI}{\CJKfamily{kai}}
\newcommand{\HEI}{\CJKfamily{hei}}

\RequirePackage[toc, page, title, titletoc, header]{appendix}
\RequirePackage{paralist}
\RequirePackage{amsthm, amsfonts}
\RequirePackage{amsmath, bm}
\RequirePackage{amssymb, mathrsfs}
\RequirePackage{latexsym}
\RequirePackage{longtable, multirow, hhline, tabularx, array}
\RequirePackage{flafter}
\RequirePackage{pifont, calc}
\RequirePackage{colortbl, booktabs}
\RequirePackage{geometry}
\RequirePackage[T1]{fontenc}
\RequirePackage[scaled]{berasans}
\RequirePackage{hyperref}
\geometry{top=25.4mm,bottom=25.4mm,left=25mm,headsep=5mm,right=25mm}
\RequirePackage{ifpdf, ifxetex}
\ifMCM@opt@CTeX
\else
  \RequirePackage{environ}
\fi
\ifpdf
  \RequirePackage{graphicx}
  \RequirePackage{epstopdf}
\else
  \ifxetex
    \RequirePackage{graphicx}
  \else
    \RequirePackage[dvipdfmx]{graphicx}
    \RequirePackage{bmpsize}
  \fi
\fi
\RequirePackage[svgnames]{xcolor}
\ifpdf
  \hypersetup{hidelinks}
\else
  \ifxetex
    \hypersetup{hidelinks}
  \else
    \hypersetup{dvipdfm, hidelinks}
  \fi
\fi
\geometry{top=25.4mm,bottom=25.4mm,left=25mm,headsep=5mm,right=25mm}
\pagestyle{fancy}
\fancyhf{}
\lhead{\small\sffamily \team}
\rhead{\small\sffamily 全国大学生数学建模竞赛}
\cfoot{\xiaowuhao\sffamily \thepage}
\setlength\parskip{1.5\baselineskip}
\renewcommand\tableofcontents{%
    \centerline{\normalfont\Large\bfseries\contentsname
        \@mkboth{%
           \MakeUppercase\contentsname}{\MakeUppercase\contentsname}}%
    \vskip 5ex%
    \@starttoc{toc}%
    }
\setcounter{totalnumber}{4}
\setcounter{topnumber}{2}
\setcounter{bottomnumber}{2}
\renewcommand{\textfraction}{0.15}
\renewcommand{\topfraction}{0.85}
\renewcommand{\bottomfraction}{0.65}
\renewcommand{\floatpagefraction}{0.60}
\renewcommand{\figurename}{\song\wuhao 图}
\renewcommand\tablename{\song\wuhao 表}
\graphicspath{{./}{./img/}{./fig/}{./image/}{./figure/}{./picture/}
            {./imgs/}{./figs/}{./images/}{./figures/}{./pictures/}}
\def\maketitle{%
  \pagestyle{empty}
  \let\saved@thepage\thepage
  \let\thepage\relax
  \ifMCM@opt@sheet
    \ifMCM@opt@withoutpreface\else
      \makesheet
    \fi
  \fi
  \newpage
  \let\thepage\saved@thepage
}
\def\abstractname{摘\quad 要}
\ifMCM@opt@CTeX
  \newbox\@abstract%
  \setbox\@abstract\hbox{}%
  \long\def\abstract{\bgroup\global\setbox\@abstract\vbox\bgroup\hsize\textwidth\leftskip1cm\rightskip1cm\parindent=2em}%
  \def\endabstract{\egroup\egroup}
  \def\make@abstract{%
    \begin{center}
      \textbf{\abstractname}
    \end{center}
    \usebox\@abstract\par
  }
\else
  \RenewEnviron{abstract}{\xdef\@abstract{\expandonce\BODY}}
  \def\make@abstract{%
      \centerline{\sanhao\HEI\textbf{摘\quad 要}}
    \@abstract\par
  }
\fi

\def\keywordsname{关键词}
\ifMCM@opt@CTeX
  \newbox\@keywords
  \setbox\@keywords\hbox{}
  \def\keywords{\global\setbox\@keywords\vbox\bgroup\noindent\leftskip0cm}
  \def\endkeywords{\egroup}%
  \def\make@keywords{%
   \par\hskip.4cm\textbf{\keywordsname}：\usebox\@keywords\hfill\par
  }
\else
  \NewEnviron{keywords}{\xdef\@keywords{\expandonce\BODY}}
  \def\make@keywords{%
    \par\noindent\sihao\textbf{关键词}：
    \@keywords\par
  }
\fi

% ═══════════════════ 封面页（国赛标准：承诺书+编号页） ═══════════════════
\newcommand{\headset}{{\the\year} 年高教社杯全国大学生数学建模竞赛}
\newcommand{\problem}[1]{\mcmsetup{problem = #1}}

% 承诺书（第1页）
\def\makecommitment{%
  \thispagestyle{empty}%
  \begin{center}
    {\LARGE\HEI\textbf{参 赛 承 诺 书}}
  \end{center}
  \vspace{1cm}
  {\song\xiaosihao
  我们仔细阅读了《全国大学生数学建模竞赛章程》和《全国大学生数学建模竞赛参赛规则》（以下简称为''竞赛章程和参赛规则''，可从全国大学生数学建模竞赛网站下载）。

  我们完全明白，在竞赛开始后参赛队员不能以任何方式（包括电话、电子邮件、网上咨询等）与队外的任何人（包括指导教师）研究、讨论与赛题有关的问题。

  我们知道，抄袭别人的成果是违反竞赛章程和参赛规则的，如果引用别人的成果或其他公开的资料（包括网上查到的资料），必须按照规定的参考文献的表述方式在正文引用处和参考文献中明确列出。

  我们郑重承诺，严格遵守竞赛章程和参赛规则，以保证竞赛的公正、公平性。如有违反竞赛章程和参赛规则的行为，我们将受到严肃处理。

  我们授权全国大学生数学建模竞赛组委会，可将我们的论文以任何形式进行公开展示（包括进行网上公示，在书籍、期刊和其他媒体进行正式或非正式发表等）。
  }
  \vspace{1.5cm}
  {\song\xiaosihao
  \noindent 我们参赛选择的题号是（从A/B/C/D/E中选择一项填写）： \underline{\hspace{3cm}}\\
  我们的参赛报名号为： \underline{\hspace{5cm}}\\
  \vspace{1cm}
  \noindent 参赛队员 (签名) ：\\
  队员1： \underline{\hspace{5cm}}\\
  队员2： \underline{\hspace{5cm}}\\
  队员3： \underline{\hspace{5cm}}\\
  \vspace{0.8cm}
  \noindent 指导教师或指导教师组负责人 (签名)：\\
  \underline{\hspace{5cm}}\\
  \vspace{0.8cm}
  \noindent 日期： \underline{\hspace{2cm}} 年 \underline{\hspace{1cm}} 月 \underline{\hspace{1cm}} 日
  }
  \newpage
}

% 编号专用页（第2页）
\def\makenumbering{%
  \thispagestyle{empty}%
  \vspace*{2cm}
  \begin{center}
    {\LARGE\HEI\textbf{编 号 专 用 页}} \\[1cm]
    {\large 赛区评阅编号（由赛区组委会评阅前进行编号）：}
  \end{center}
  \vspace{3cm}
  \begin{center}
    {\large 全国统一编号（由赛区组委会送交全国前编号）：}
  \end{center}
  \newpage
}

% 封面+编号页（第1-2页，纸质版）
\def\makesheet{%
  \makecommitment
  \makenumbering
}

\def\MCM@maketitle{%
  \begin{center}%
  \let \footnote \thanks
    {\LARGE \@title \par}%
    \vskip 1.5em%
    {\large
      \lineskip .5em%
      \begin{tabular}[t]{c}%
        \@author
      \end{tabular}\par}%
    \vskip 1em%
    {\large \@date}%
  \end{center}%
  \par
  \vskip 1.5em%
  \ifMCM@opt@abstract%
    \make@abstract
    \make@keywords
  \fi%
}

% =================================================================
% 定理环境
% =================================================================
\newtheorem{Theorem}{\HEI 定理}[section]
\newtheorem{Lemma}[Theorem]{\HEI 引理}
\newtheorem{Corollary}[Theorem]{\HEI 推论}
\newtheorem{Proposition}[Theorem]{\HEI 命题}
\newtheorem{Definition}[Theorem]{\HEI 定义}
\newtheorem{Example}[Theorem]{\HEI 例}
\newtheorem{rmk}{\hskip\parindent\heiti 注}

% =================================================================
% 图表编号
% =================================================================
\renewcommand{\thefigure}{\ifnum \c@section>\z@ \arabic{section}-\fi \@arabic\c@figure}
\renewcommand{\thetable}{\ifnum \c@section>\z@ \arabic{section}-\fi \@arabic\c@table}

% =================================================================
% 代码抄录
% =================================================================
\definecolor{grey}{rgb}{0.8,0.8,0.8}
\definecolor{darkgreen}{rgb}{0,0.3,0}
\definecolor{darkblue}{rgb}{0,0,0.3}
\def\lstbasicfont{\ttfamily\footnotesize}
\lstset{%
    showstringspaces=false,
    showspaces=false,%
    tabsize=4,%
    frame=lines,%
    basicstyle={\footnotesize\lstbasicfont},%
    keywordstyle=\color{darkblue}\bfseries,%
    identifierstyle=,%
    commentstyle=\color{darkgreen},%
    stringstyle=\color{black}%
}
\lstloadlanguages{C,C++,Java,Matlab,Mathematica}
\endinput
