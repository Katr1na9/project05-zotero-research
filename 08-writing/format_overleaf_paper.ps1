param(
    [string]$Source = 'C:\Users\35393\.codex\attachments\05bd4e5c-caaa-41ae-a408-dd18cff4fda6\pasted-text.txt',
    [string]$Output = (Join-Path $PSScriptRoot 'Project05-overleaf-cybersecurity-paper.tex')
)

$ErrorActionPreference = 'Stop'
$sourceText = Get-Content -LiteralPath $Source -Raw -Encoding UTF8
$bodyMatch = [regex]::Match($sourceText, '(?s)\\begin\{document\}\s*(.*?)\\end\{document\}')
if (-not $bodyMatch.Success) {
    throw 'Could not locate the LaTeX document body.'
}
$body = $bodyMatch.Groups[1].Value.Trim()

# Pull the four result tables out of the malformed tail so they can be placed
# beside their first discussion in the paper.
$tableMatches = [regex]::Matches($body, '(?s)\\begin\{table\}\[h\].*?\\end\{table\}')
if ($tableMatches.Count -ne 4) {
    throw "Expected four tables, found $($tableMatches.Count)."
}
$rawTables = @($tableMatches | ForEach-Object { $_.Value })
$body = [regex]::Replace($body, '(?s)\s*\\begin\{table\}\[h\].*?\\end\{table\}', '')

function Convert-Table {
    param([string]$Raw, [string]$Caption, [string]$Label)
    $tabular = [regex]::Match($Raw, '(?s)\\begin\{tabular\}.*?\\end\{tabular\}').Value
    return @"
\begin{table*}[t]
  \centering
  \caption{$Caption}
  \label{$Label}
  \resizebox{\textwidth}{!}{%
$tabular
  }
\end{table*}
"@
}

$tables = @(
    (Convert-Table $rawTables[0] '成本 profile 的语义、状态与解释边界' 'tab:cost-profiles'),
    (Convert-Table $rawTables[1] '冻结 legacy 成本下的 ML 正式入口结果' 'tab:legacy-results'),
    (Convert-Table $rawTables[2] '单位成本口径下各正式入口的平均动作数' 'tab:uniform-results'),
    (Convert-Table $rawTables[3] '参数治理扫描与动作序列稳定性' 'tab:governance-scan')
)

# Replace the duplicate free-standing title and convert the abstract/keywords
# into IEEE environments.
$abstractStart = $body.IndexOf('\section*{摘要}')
if ($abstractStart -lt 0) { throw 'Abstract marker not found.' }
$body = "\maketitle`r`n`r`n\begin{abstract}" + $body.Substring($abstractStart + '\section*{摘要}'.Length)
$body = [regex]::Replace(
    $body,
    '(?m)^关键词：(.*?)\r?\n\s*\r?\n1 引言\s*$',
    "\end{abstract}`r`n`r`n\begin{IEEEkeywords}`r`n`$1`r`n\end{IEEEkeywords}`r`n`r`n\section{引言}"
)

# Convert all remaining numeric headings to semantic LaTeX headings.
$body = [regex]::Replace($body, '(?m)^([1-9])\.([1-9])\s+(.+?)\s*$', '\subsection{$3}')
$body = [regex]::Replace($body, '(?m)^([1-9])\s+(.+?)\s*$', '\section{$2}')
$body = $body.Replace('\section{ 参数治理与实现 }', '\section{参数治理与实现}')
$body = $body.Replace('\subsection{ k-of-n corroboration 与支持上限 }', '\subsection{k-of-n corroboration 与支持上限}')
$body = $body.Replace('\subsection{ 信息边界 }', '\subsection{信息边界}')
$body = $body.Replace('\subsection{ 决策、反馈和停止 }', '\subsection{决策、反馈和停止}')
$body = $body.Replace('\subsection{ 成本 profile }', '\subsection{成本 profile}')
$body = $body.Replace('\subsection{ 收益权重与先验 profile }', '\subsection{收益权重与先验 profile}')

# Format the four stated contributions as a compact numbered list.
$contribPattern = '(?s)(因此，本稿把贡献组织为四点：)\s*(.*?)\s*(\\section\{相关工作与任务边界\})'
$contribMatch = [regex]::Match($body, $contribPattern)
if ($contribMatch.Success) {
    $items = $contribMatch.Groups[2].Value -split '\r?\n\s*\r?\n' | Where-Object { $_.Trim() }
    $list = "`r`n`r`n\begin{enumerate}[leftmargin=*,label=(\arabic*)]`r`n" + (($items | ForEach-Object { "  \item $($_.Trim())" }) -join "`r`n") + "`r`n\end{enumerate}`r`n`r`n"
    $body = $body.Substring(0, $contribMatch.Index) + $contribMatch.Groups[1].Value + $list + $contribMatch.Groups[3].Value + $body.Substring($contribMatch.Index + $contribMatch.Length)
}

# Format the limitations as a review-friendly enumerated list.
$limitsPattern = '(?s)(\\section\{局限性与开放 Gate\})\s*(.*?)\s*(\\section\{结论\})'
$limitsMatch = [regex]::Match($body, $limitsPattern)
if ($limitsMatch.Success) {
    $items = $limitsMatch.Groups[2].Value -split '\r?\n\s*\r?\n' | Where-Object { $_.Trim() }
    $list = "`r`n`r`n\begin{enumerate}[leftmargin=*,label=(\arabic*)]`r`n" + (($items | ForEach-Object { "  \item $($_.Trim())" }) -join "`r`n") + "`r`n\end{enumerate}`r`n`r`n"
    $body = $body.Substring(0, $limitsMatch.Index) + $limitsMatch.Groups[1].Value + $list + $limitsMatch.Groups[3].Value + $body.Substring($limitsMatch.Index + $limitsMatch.Length)
}

# Place the tables at their first point of interpretation.
$body = $body.Replace('运行器支持四种成本口径：', "运行器支持四种成本口径：`r`n`r`n$($tables[0])")
$body = $body.Replace('在统一的 C07–C12 ML 正式入口中：', "在统一的 C07–C12 ML 正式入口中：`r`n`r`n$($tables[1])")
$body = $body.Replace('三个正式入口得到：', "三个正式入口得到：`r`n`r`n$($tables[2])")
$body = $body.Replace('\subsection{阈值、corroboration 与 α 稳健性}', "\subsection{阈值、corroboration 与 \texorpdfstring{`$\alpha`$}{alpha} 稳健性}`r`n`r`n$($tables[3])")

# Add the referenced information-boundary schematic as native TikZ so the
# Overleaf project remains a single file.
$figureAnchor = '图 1 展示调查控制闭环与信息边界。规划器仅访问公开动作目标、成本、当前缺口、预算及历史反馈；执行器和 Oracle 隐藏实际恢复集合与实现通道状态。'
$figure = @'

\begin{figure*}[t]
  \centering
  \begin{tikzpicture}[
    font=\small,
    node distance=9mm and 11mm,
    box/.style={draw, rounded corners=2pt, minimum height=10mm, minimum width=30mm, align=center, fill=blue!4},
    hidden/.style={box, fill=red!5, draw=red!65!black},
    flow/.style={-{Latex[length=2.2mm]}, thick},
    feedback/.style={-{Latex[length=2.2mm]}, thick, dashed, teal!70!black}
  ]
    \node[box] (state) {公开调查状态\\证据缺口、预算、历史};
    \node[box, right=of state] (planner) {非 Oracle 规划器\\选择 action\_id 或 STOP};
    \node[hidden, right=of planner] (executor) {执行器\\读取完整动作并采集};
    \node[box, right=of executor] (evidence) {反馈与状态更新\\新增 claims 或零收益};
    \node[hidden, below=of executor] (oracle) {隐藏域\\$R(a)$、真实通道状态、结果标签};

    \draw[flow] (state) -- node[above]{公开视图} (planner);
    \draw[flow] (planner) -- node[above]{action\_id} (executor);
    \draw[flow] (executor) -- node[above]{采集结果} (evidence);
    \draw[flow, red!65!black] (oracle) -- (executor);
    \draw[feedback] (evidence.south) to[out=-110,in=-70] node[below]{可审计反馈} (state.south);

    \node[draw=blue!65!black, dashed, rounded corners, fit=(state)(planner), inner sep=5pt,
          label=above:{\bfseries 规划器可见域}] {};
    \node[draw=red!65!black, dashed, rounded corners, fit=(executor)(oracle), inner sep=5pt,
          label=above:{\bfseries 执行/Oracle 隐藏域}] {};
  \end{tikzpicture}
  \caption{调查控制闭环与信息边界。规划器只读取执行前公开且版本化的状态；隐藏恢复集合和真实通道状态仅在动作选定后由执行器访问。}
  \label{fig:control-loop}
\end{figure*}
'@
$body = $body.Replace($figureAnchor, $figureAnchor.Replace('图 1', '图~\ref{fig:control-loop}') + $figure)

# Split and convert numbered references, while converting bracketed citations
# only in the main text.
$refMarker = "`r`n参考文献`r`n"
$refIndex = $body.IndexOf($refMarker)
if ($refIndex -lt 0) {
    $refMarker = "`n参考文献`n"
    $refIndex = $body.IndexOf($refMarker)
}
if ($refIndex -lt 0) { throw 'Reference section marker not found.' }
$main = $body.Substring(0, $refIndex)
$refs = $body.Substring($refIndex + $refMarker.Length).Trim()
$main = [regex]::Replace($main, '\[(\d+(?:\s*,\s*\d+)*)\]', {
    param($m)
    $keys = ($m.Groups[1].Value -split '\s*,\s*' | ForEach-Object { "ref$_" }) -join ','
    return "\cite{$keys}"
})
$refs = [regex]::Replace($refs, '(?m)^\[(\d+)\]\s*', '\bibitem{ref$1} ')
$refs = $refs.Replace('Sch\textbackslash\{\}"utz', 'Sch\"{u}tz')
$refs = [regex]::Replace($refs, 'https?://[^\s]+', { param($m) "\url{$($m.Value)}" })
$refs = [regex]::Replace($refs, 'doi:([0-9][^\s]+)', { param($m) "doi:\url{https://doi.org/$($m.Groups[1].Value)}" })

$main = $main.Replace('all\_experiments\_complete=false', '\texttt{all\_experiments\_complete=false}')
$main = $main.Replace('external\_actor\_accuracy', '\texttt{external\_actor\_accuracy}')
$main = $main.Replace('not\_identifiable', '\texttt{not\_identifiable}')
$main = $main.Replace('support\_ceiling', '\texttt{support\_ceiling}')
$main = $main.Replace('action\_id', '\texttt{action\_id}')
$main = $main.Replace('acquisition\_actions.json', '\texttt{acquisition\_actions.json}')
$main = $main.Replace('κ=-0.1455', '$\kappa=-0.1455$')
$main = $main.Replace('M2 α', 'M2 $\alpha$')
$main = [regex]::Replace($main, '(?m)^数据与代码可用性\s*$', '\section*{数据与代码可用性}')
$main = $main.Replace('github 仓库', 'GitHub 仓库')
$main = $main.Replace('，而POIROT', '，而 POIROT')
$main = $main.Replace('actor或campaign', 'actor 或 campaign')
$main = $main.Replace('I(a)=Cover(R(a))', 'I(a)=\operatorname{Cover}(R(a))')
$main = $main.Replace('V^*(s'')', 'V^\star(s'')')
$main = $main.Replace('a\neq STOP', 'a\neq \mathrm{STOP}')

$preamble = @'
\documentclass[conference,a4paper,10pt]{IEEEtran}

% Overleaf: Menu -> Compiler -> XeLaTeX
\usepackage[UTF8,fontset=fandol,scheme=plain]{ctex}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{xurl}
\usepackage{cite}
\usepackage{balance}
\usepackage{xcolor}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,fit}
\usepackage[hidelinks,unicode]{hyperref}

\hypersetup{
  pdftitle={不完整证据下的可审计 APT 调查控制：信息边界、参数治理与证据获取},
  pdfauthor={匿名作者},
  pdfkeywords={APT 调查, 不完整证据, 主动取证, 信息边界, 参数治理}
}
\urlstyle{same}
\renewcommand{\abstractname}{摘要}
\renewcommand{\IEEEkeywordsname}{关键词}
\renewcommand{\figurename}{图}
\renewcommand{\tablename}{表}
\setlist{nosep}

\title{不完整证据下的可审计 APT 调查控制：\\
信息边界、参数治理与证据获取\\[-0.1em]
{\large Auditable APT Investigation Control under Incomplete Evidence:\\
Information Boundaries, Parameter Governance, and Evidence Acquisition}}

% 双盲投稿时保留匿名信息；终稿请替换为真实作者、单位和邮箱。
\author{\IEEEauthorblockN{匿名作者}
\IEEEauthorblockA{匿名单位\\anonymous@example.com}}

\begin{document}
'@

$ending = @'

\balance
\begin{thebibliography}{99}
'@ + "`r`n" + $refs + @'

\end{thebibliography}
\end{document}
'@

$outputText = $preamble + "`r`n" + $main.Trim() + "`r`n" + $ending
[System.IO.File]::WriteAllText($Output, $outputText, [System.Text.UTF8Encoding]::new($false))
Write-Output $Output
