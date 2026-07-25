param(
    [string]$Source = 'C:\Users\35393\.codex\attachments\efc27103-afbc-4716-abb4-22afa1102f35\pasted-text.txt',
    [string]$Output = (Join-Path $PSScriptRoot 'Project05-overleaf-figures-tables-revised.tex')
)

$ErrorActionPreference = 'Stop'
$text = Get-Content -LiteralPath $Source -Raw -Encoding UTF8

# Remove the original floating blocks. They are rebuilt below and inserted
# immediately after the paragraphs that first discuss them.
$floatPattern = '(?s)\\begin\{(?:figure|table)\*\}\[t\].*?\\end\{(?:figure|table)\*\}'
$oldFloats = [regex]::Matches($text, $floatPattern)
if ($oldFloats.Count -ne 5) {
    throw "Expected five figure/table floats, found $($oldFloats.Count)."
}
$text = [regex]::Replace($text, "\r?\n*$floatPattern\r?\n*", "`r`n`r`n")

# Publication-oriented packages and shared styling. The palette uses
# Okabe--Ito blue/orange/green and redundant line styles for grayscale use.
$text = $text.Replace('\usepackage{graphicx}', "\usepackage{graphicx}`r`n\usepackage[table]{xcolor}")
$text = $text.Replace('\usepackage{booktabs,tabularx,array,multirow}', "\usepackage{booktabs,tabularx,array,multirow}`r`n\usepackage{makecell}`r`n\usepackage{dblfloatfix}`r`n\usepackage[section]{placeins}")
$text = $text.Replace('\usetikzlibrary{arrows.meta,positioning,fit,calc}', '\usetikzlibrary{arrows.meta,positioning,fit,calc}')

$oldCaptionBlock = @'
\captionsetup{
  font=small,
  labelfont=normalfont,
  textfont=normalfont,
  justification=centering,
  singlelinecheck=false,
  skip=3pt
}
\captionsetup[figure]{labelsep=period}
\captionsetup[table]{labelsep=newline,position=top}
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\thetable}{\Roman{table}}

\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
'@

$newCaptionBlock = @'
% ===== Publication-ready figure and table style =====
\definecolor{oiBlue}{HTML}{0072B2}
\definecolor{oiOrange}{HTML}{E69F00}
\definecolor{oiGreen}{HTML}{009E73}
\definecolor{softBlue}{HTML}{EAF3F8}
\definecolor{softOrange}{HTML}{FFF3DF}
\definecolor{softGreen}{HTML}{EAF6F1}
\definecolor{softGray}{HTML}{F1F3F5}
\definecolor{tableHeader}{HTML}{E8EDF2}

\captionsetup{
  font=small,
  labelfont=bf,
  textfont=normalfont,
  format=plain,
  justification=justified,
  singlelinecheck=true,
  skip=4pt
}
\captionsetup[figure]{labelsep=quad,position=bottom}
\captionsetup[table]{labelsep=quad,position=top}
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\renewcommand{\thetable}{\arabic{table}}

\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcolumntype{C}{>{\centering\arraybackslash}X}
\setlength{\heavyrulewidth}{0.8pt}
\setlength{\lightrulewidth}{0.45pt}
\setlength{\cmidrulewidth}{0.4pt}
\newcommand{\publishtable}{%
  \small
  \setlength{\tabcolsep}{4pt}%
  \renewcommand{\arraystretch}{1.16}%
  \arrayrulecolor{black!75}%
}
'@

if (-not $text.Contains($oldCaptionBlock)) {
    throw 'Original caption style block was not found.'
}
$text = $text.Replace($oldCaptionBlock, $newCaptionBlock)

$figure = @'
\begin{figure*}[!t]
  \centering
  \begin{tikzpicture}[
    >=Latex,
    node distance=9mm and 8mm,
    font=\small,
    base/.style={draw, rounded corners=2pt, align=center, minimum height=13mm,
                 text width=33mm, inner sep=3.5pt, line width=0.6pt},
    public/.style={base, draw=oiBlue, fill=softBlue},
    execute/.style={base, draw=oiOrange!85!black, fill=softOrange},
    update/.style={base, draw=oiGreen!80!black, fill=softGreen},
    hidden/.style={base, draw=black!65, fill=softGray, dashed},
    flow/.style={-{Latex[length=2.2mm]}, line width=0.7pt, draw=black!80},
    feedback/.style={-{Latex[length=2.2mm]}, line width=0.7pt, dashed, draw=oiGreen!80!black},
    hiddenflow/.style={-{Latex[length=2.2mm]}, line width=0.7pt, densely dashed, draw=black!65},
    boundary/.style={rounded corners=3pt, dashed, line width=0.55pt, inner sep=4mm}
  ]
    \node[public] (state) {公开调查状态\\证据缺口、预算、历史};
    \node[public, right=of state] (planner) {非预知器规划器\\选择动作标识符或 STOP};
    \node[execute, right=of planner] (executor) {执行器\\读取完整动作并采集};
    \node[update, right=of executor] (feedback) {反馈与状态更新\\新增证据声明或零收益};
    \node[hidden, below=12mm of executor] (hidden) {隐藏域\\实际恢复集合、真实通道状态、结果标签};

    \draw[flow] (state) -- node[above,font=\scriptsize]{公开视图} (planner);
    \draw[flow] (planner) -- node[above,font=\scriptsize]{动作标识符} (executor);
    \draw[flow] (executor) -- node[above,font=\scriptsize]{采集结果} (feedback);
    \draw[hiddenflow] (hidden) -- node[right,font=\scriptsize]{执行后访问} (executor);
    \draw[feedback] (feedback.south) |- ([yshift=-9mm]hidden.south) -|
      node[pos=0.82,below,font=\scriptsize]{可审计反馈} (state.south);

    \node[boundary, draw=oiBlue, fit=(state)(planner),
          label={[font=\scriptsize\bfseries,text=oiBlue]below:规划器可见域}] {};
    \node[boundary, draw=black!65, fit=(executor)(hidden),
          label={[font=\scriptsize\bfseries]below:执行器/预知器隐藏域}] {};
  \end{tikzpicture}
  \caption{调查控制闭环与信息边界。实线表示公开控制流，虚线表示受限访问或执行后反馈；规划器无法在动作选定前读取实际恢复集合与真实通道状态。}
  \label{fig:control-loop}
\end{figure*}
'@

$costTable = @'
\begin{table*}[!t]
  \caption{成本配置文件的语义、状态与解释边界}
  \label{tab:cost-profile}
  \centering
  \publishtable
  \begin{tabularx}{\textwidth}{@{}>{\bfseries}lYYY@{}}
    \toprule
    \rowcolor{tableHeader}
    配置文件 & \textbf{含义} & \textbf{当前状态} & \textbf{可作何种解释} \\
    \midrule
    历史基线 & 原案例中的历史相对成本 & 正式运行完成；与旧输出逐字节兼容 & 冻结历史基线，不代表真实运营成本 \\
    \addlinespace[2pt]
    单位成本（uniform） & 所有非 STOP 动作为 1 & 正式运行完成 & 动作步数对照，去除人工成本排序 \\
    \addlinespace[2pt]
    评分量表（rubric） & 由工作量（E）、易失性（V）、数据量（D）、访问合规性（A）和侵入风险（R）五个分量构成 & 360 个独立人工评分分量待完成 & 冻结前不得进入正式实验 \\
    \addlinespace[2pt]
    实测成本（measured） & 动作级运营测量归一化后的连续成本 & 72/72 动作待测；基础设施已完成 & 当前不得报告数值或替代真实成本 \\
    \bottomrule
  \end{tabularx}
\end{table*}
'@

$legacyTable = @'
\begin{table*}[!t]
  \caption{冻结的历史基线成本下的机器学习正式入口结果}
  \label{tab:legacy-ml}
  \centering
  \publishtable
  \begin{tabularx}{\textwidth}{@{}lCCCY@{}}
    \toprule
    \rowcolor{tableHeader}
    \textbf{规划器} & \textbf{达标条件} & \textbf{成功率} & \makecell[c]{\textbf{成功条件下}\\\textbf{平均成本}} & \textbf{解释} \\
    \midrule
    XGBoost & 270/270 & 1.0000 & 3.8926 & 冻结训练、公开特征 \\
    M2 & 270/270 & 1.0000 & 3.8704 & 透明部署锚点 \\
    Logistic/M3b & 267/270 & 0.9889 & 4.0000 & 3 个失败均保留 \\
    \bottomrule
  \end{tabularx}
\end{table*}
'@

$uniformTable = @'
\begin{table*}[!t]
  \caption{单位成本口径下各正式入口的平均动作数}
  \label{tab:uniform-cost}
  \centering
  \publishtable
  \begin{tabularx}{\textwidth}{@{}lYCC@{}}
    \toprule
    \rowcolor{tableHeader}
    \textbf{正式入口} & \textbf{规划器} & \textbf{达标条件} & \makecell[c]{\textbf{单位成本下}\\\textbf{平均成本}} \\
    \midrule
    \multirow{4}{*}{AFA}
      & M2 & 270/270 & 1.7296 \\
      & AFA-VOI Myopic & 270/270 & 1.7333 \\
      & AFA-VOI Rollout-H3 & 270/270 & 1.7778 \\
      & Oracle & 270/270 & 1.4852 \\
    \addlinespace[2pt]
    \cmidrule(lr){1-4}
    \multirow{3}{*}{Depth-2}
      & M2 & 270/270 & 1.7296 \\
      & Depth-2 & 270/270 & 1.8963 \\
      & Oracle & 270/270 & 1.4852 \\
    \addlinespace[2pt]
    \cmidrule(lr){1-4}
    \multirow{5}{*}{ML}
      & XGBoost & 270/270 & 1.6852 \\
      & Logistic/M3b & 270/270 & 1.6630 \\
      & M2 & 270/270 & 1.7296 \\
      & M3a & 270/270 & 1.7333 \\
      & Oracle & 270/270 & 1.4852 \\
    \bottomrule
  \end{tabularx}
\end{table*}
'@

$governanceTable = @'
\begin{table*}[!t]
  \caption{参数治理扫描与动作序列稳定性}
  \label{tab:governance-scan}
  \centering
  \publishtable
  \begin{tabularx}{\textwidth}{@{}YCCCC@{}}
    \toprule
    \rowcolor{tableHeader}
    \textbf{治理项} & \textbf{变体数} & \makecell[c]{\textbf{M2 成功率}\\\textbf{范围}} & \makecell[c]{\textbf{最低动作序列}\\\textbf{一致率}} & \makecell[c]{\textbf{最大粒度}\\\textbf{越界率}} \\
    \midrule
    成本（历史基线/单位成本） & 2 & 1.0000--1.0000 & 0.9111 & 0 \\
    G3 阈值网格 & 40 & 1.0000--1.0000 & 1.0000 & 0 \\
    n 项证据中至少 k 项相互印证 & 6 & 1.0000--1.0000 & 0.8148 & 0 \\
    M2 $\alpha$ & 7 & 1.0000--1.0000 & 0.8407 & 0 \\
    \bottomrule
  \end{tabularx}
\end{table*}
'@

$anchors = @{
    Figure = '图~\ref{fig:control-loop} 展示调查控制闭环与信息边界。规划器仅访问公开动作目标、成本、当前缺口、预算及历史反馈；执行器和 Oracle 隐藏域保存实际恢复集合与实现通道状态。'
    Cost = '运行器支持四种成本口径，如表~\ref{tab:cost-profile} 所示。'
    Legacy = '在统一的 C07--C12 机器学习（ML）正式入口中，结果如表~\ref{tab:legacy-ml} 所示。这些数字使用历史相对成本，只能回答冻结实现下发生了什么，不能回答真实运营中哪个规划器更便宜。'
    Uniform = '单位成本配置文件把每个非 STOP 动作成本固定为 1，因此平均成本等于平均动作数。三个正式入口得到表~\ref{tab:uniform-cost} 所示结果。'
    Governance = '表~\ref{tab:governance-scan} 汇总参数治理扫描与动作序列稳定性。'
}

foreach ($key in $anchors.Keys) {
    if (-not $text.Contains($anchors[$key])) {
        throw "Insertion anchor '$key' was not found."
    }
}

$text = $text.Replace($anchors.Figure, $anchors.Figure + "`r`n`r`n" + $figure)
$text = $text.Replace($anchors.Cost, $anchors.Cost + "`r`n`r`n" + $costTable)
$text = $text.Replace($anchors.Legacy, $anchors.Legacy + "`r`n`r`n" + $legacyTable)
$text = $text.Replace($anchors.Uniform, $anchors.Uniform + "`r`n`r`n" + $uniformTable)
$text = $text.Replace($anchors.Governance, $anchors.Governance + "`r`n`r`n" + $governanceTable)

# Keep wide result tables within the Results section rather than letting them
# drift into Discussion or the reference list.
$text = $text.Replace("`r`n\newpage`r`n\section{讨论}", "`r`n\FloatBarrier`r`n\newpage`r`n\section{讨论}")
$text = $text.Replace("`r`n\section{实验设计}", "`r`n\FloatBarrier`r`n\section{实验设计}")

# Reduce accidental runs of blank lines introduced by moving floats.
$text = [regex]::Replace($text, '(\r?\n){4,}', "`r`n`r`n`r`n")
[System.IO.File]::WriteAllText($Output, $text, [System.Text.UTF8Encoding]::new($false))
Write-Output $Output
