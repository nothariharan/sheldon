> Public quotes, kept as research notes.
> Do not copy any quote from this file into the README or UI text until someone has opened that quote's link.
> The Reddit quotes were taken from the arctic-shift archive and have not been checked against the live thread.
>
> **Precedence:** [`facts.md`](../facts.md), [`REPORT.md`](../decisions/REPORT.md), and [`papers.md`](../engine/papers.md) override this file.

# pains.md: real problems people had with ai agents, jul 17 to oct 17 2026

updated 2026-10-17 11:05 IST · pain-finder

window: 2026-07-17 to 2026-10-17 inclusive. every quote below is verbatim, linked, and dated inside the window. "…" marks where i cut a quote (end only) or where the post itself is cut off by the x api. x engagement = likes / replies / reposts. hn comment scores aren't exposed by the api, so hn engagement = n/a. github = reactions / comments. reddit = score / comments (via arctic-shift, created_utc checked).

sources: x (search_posts_all, 17 calls), hn (algolia, comments+stories after epoch 1784246400), github issues (claude-code, langgraph, crewai, autogen, mem0, letta), reddit (r/ClaudeAI, r/AI_Agents, r/cursor, r/sre, r/ExperiencedDevs via arctic-shift; reddit.com json is blocked).

totals: 96 quote entries kept (91 distinct posts; a few posts are quoted in two clusters). 3 dropped for date (reddit posts from jun 19, jul 11, feb 8). about 17 more x posts dropped because they retell prod-db-wipe incidents that happened before the window (pocketos apr 2026, replit jul 2025), even though the posts themselves are in-window.

sheldon in one line (from SHELDON_REPORT.md §1, PLAN §3/§7): append-only event log + hypothesis/decision nodes + a task board (atomic claim, lease, handoff, resume) on one falkordb graph per incident investigation. `resume()` returns what was tried, what failed and why, what's believed, what's next, all with cited event ids. `check_prior_attempts(task)` returns earlier action → result pairs. causal links start as `proposed` and only become `confirmed` by a rule or sign-off. answers come with the traversal path.

---

## ranked clusters

| # | cluster | quotes | verdict |
|---|---|---|---|
| 1 | forgets across sessions / compaction eats the context | 19 | partly solves |
| 2 | re-tries what already failed, re-proposes ruled-out approaches | 15 | solves |
| 3 | handoffs drop context (agent→agent, tool→tool) | 14 | solves |
| 4 | runaway loops burning tokens/money (often with numbers) | 10 | partly solves |
| 5 | stale or corrected memory keeps getting acted on | 13 | partly solves (solves if Q* ships) |
| 6 | can't explain why it acted / claims "done" with no evidence | 12 | solves |
| 7 | on-call / incident pain with ai tools | 9 | partly solves |
| 8 | agents taking destructive actions in prod (side note) | 4 | doesn't touch |

ranking = how many quotes i found + how angry they read. 1 and 2 are the loudest. 2, 3 and 6 match sheldon best. **the "can't explain why" cluster (6) is thinner than it looks:** lots of commentary about audit trails, few first-person "it couldn't tell me why" posts. **repeated failed steps (2+4) is not thin:** many first-person posts, several with hard numbers.

---

## 1. forgets across sessions / compaction eats the context
the agent loses decisions, constraints and in-progress state when a session ends or auto-compaction runs.
quotes: 19 · **verdict: partly solves.** sheldon's append-only event chain + `IN_SESSION` provenance + `resume()` (PLAN §1 row 2, §7) make an investigation survive sessions and agents. but it's scoped to one incident-investigation graph per incident. it isn't a general coding-assistant memory and does nothing about a harness's own compaction.

- "auto-compaction eats the wrong half of the context every time. long session in Claude Code, the agent hits the limit, compacts itself, and what survives is the shape of the conversation. what dies is the part i needed. which file paths were real. what the exact error string was." · @claimedforwhat · x · https://x.com/claimedforwhat/status/2089681657909444877 · 2026-08-18 · 4/3/0
- "Overnight after updating to 2.1.286, 7 of those sessions were compacted while idle. None was close to the context limit. When I came back, each had a summary in place of its working context: my exact instructions, the reasoning behind decisions, and the methods we'd agreed on were gone from what the session actually sees. I had to rebuild the grounding by hand from the transcripts on disk." · @natefosterwarner · github anthropics/claude-code #98747 · https://github.com/anthropics/claude-code/issues/98747 · 2026-10-01 · 31 reactions / 23 comments
- "For conversations built up over months, the model comes back with a thin summary and noticeably different tone/behavior, and cannot look up the original exc…" · @nonsenseblue · github claude-code #99068 · https://github.com/anthropics/claude-code/issues/99068 · 2026-10-02 · 6 / 4
- "Compaction replaced the lead's transcript with a 4 KB stub; a 16-round reasoning census stated its write list at round 16 and none of it was written before the cut; only the summary survived." · @eyeskull2220 · github claude-code #97797 · https://github.com/anthropics/claude-code/issues/97797 · 2026-09-28 · 2 / 2
- "After compaction happens, the assistant noticeably loses track of session-specific context (configuration details, in-progress multi-step task state, prior instructions) even though the full transcript is still saved to disk." · @khidhr21-prog · github claude-code #99860 · https://github.com/anthropics/claude-code/issues/99860 · 2026-10-06 · 2 / 1
- "The continued session then ran for **a full day (~1,100 transcript lines)** with **zero** full skill listings." · @okabadayi · github claude-code #82017 · https://github.com/anthropics/claude-code/issues/82017 · 2026-07-28 · 3 / 3
- "Today I needed to re-read a multi-day design discussion from before two compaction points. The only way was to locate the right `.jsonl` by file size and mtime, then parse JSON Lines by hand (grep/jq/python) to recover my own conversation." · @fqueiro · github claude-code #82914 · https://github.com/anthropics/claude-code/issues/82914 · 2026-07-31 · 2 / 1
- "Somewhere around hour two, Claude Code forgets the open thread from hour zero. You end up with half-wired features and no memory of why." · @KalPetkoff · x · https://x.com/KalPetkoff/status/2102143079251644777 · 2026-09-21 · 0/1/0
- "They keep forgetting what we are working on, opening a new chat session clears all their context, my CLAUDE.md had like 1000 lines." · dat999zx · hn · https://news.ycombinator.com/item?id=49399942 · 2026-08-22 · n/a
- "I do care however that Claude still forgets about 14 times per week that -r with ripgrep means replace (and not recursive, like with grep). Even though it's literally spelled out in my CLAUDE.md." · jgb1984 · hn · https://news.ycombinator.com/item?id=49766791 · 2026-09-19 · n/a
- "claude code forgets by the second turn my "don't commit" prompt." · epolanski · hn · https://news.ycombinator.com/item?id=49102479 · 2026-07-29 · n/a
- "I noticed llm seem to forget partially or completely the original task when context compaction happens." · akg_67 · hn · https://news.ycombinator.com/item?id=49749867 · 2026-09-18 · n/a
- "Sol makes many avoidable mistakes and has issues with context compaction - sometimes it goes haywire after a couple compactions." · jmaker · hn · https://news.ycombinator.com/item?id=49802921 · 2026-09-22 · n/a
- "it keeps forgetting the changes it did itself; no context compaction was used" · cromka · hn · https://news.ycombinator.com/item?id=49881469 · 2026-09-28 · n/a
- "I had to keep reminding Claude about the same things over and over." · leonkatz · hn (show hn) · https://news.ycombinator.com/item?id=49099938 · 2026-07-29 · n/a
- "Every Claude Code session starts with amnesia. No memory, no recall of your architecture, your gotchas. Every morning you're re-onboarding a brilliant senior engineer from zero." · @SidSaladi · x · https://x.com/SidSaladi/status/2102855157482721338 · 2026-09-23 · 0/3/0
- "It's having to constantly remember the original task *for* the agent and decide whether it has actually finished." · u/aldi949 · reddit r/AI_Agents · https://www.reddit.com/r/AI_Agents/comments/1x2f1oq/my_coding_agent_can_write_the_code_why_am_i_still/ · 2026-10-10 · 2 / 59
- "What dies in compaction is session state: dead ends already ruled out, and the half-finished plan dropped mid-thought." · @armalo_ai · x · https://x.com/armalo_ai/status/2105851732693762539 · 2026-10-02 · 0/1/0
- "LLM agents solve running out of memory by giving themselves amnesia on purpose. They forget the 23 files they just edited, deny the commits they made, and have the cheek to gaslight you about it." · @vsletten3006 · x · https://x.com/vsletten3006/status/2084121380225007925 · 2026-08-03 · 9/4/2

## 2. re-tries what already failed, re-proposes ruled-out approaches
the next session or agent walks back into a dead end that was already tried and rejected.
quotes: 15 · **verdict: solves.** this is sheldon's core. `resume()` returns "what was tried / what failed and why" with citations, `check_prior_attempts(task)` returns earlier action → result pairs, and the eval counts a duplicated attempt when an agent repeats a prior failure with no stated reason (PLAN §7, REPORT §3.4).

- "Somewhere past the halfway point the session fills up, autocompact fires or I run /compact myself, and within a few turns Claude proposes something we already tried and threw out two hours earlier." · u/Prestigious_Grape786 · reddit r/ClaudeAI · https://www.reddit.com/r/ClaudeAI/comments/1vwy3hw/compaction_keeps_what_we_built_and_forgets_what/ · 2026-08-24 · 0 / 5
- "Compaction is decent at preserving what we built. It's bad at preserving what we decided against." · same post as above
- "watched my agent hit the same error over and over today. it kept trying the same fix and failing the same way. so i stopped it and fixed it by hand. took a few minutes. it looked busy the whole time, but it was just going in circles." · @malladiphani · x · https://x.com/malladiphani/status/2107056404540608789 · 2026-10-05 · 0/0/0
- "handoffs that carry what already failed matter more than the files list. we lost a day once because the second agent retried the same broken approach without that trail." · @sunsetsyntax · x · https://x.com/sunsetsyntax/status/2104832764407087549 · 2026-09-29 · 0/0/0
- "auto compact is the real tell, it drops the constraint that fixed the bug last time, so next session the agent doesn't remember and repeats the same broken fix." · @_alphashark_ · x · https://x.com/_alphashark_/status/2085890196386857387 · 2026-08-08 · 0/0/0
- "every new session it would: - re-propose an approach we already rejected in a PR - invent a convention nobody on the team uses - ask a question that was…" · @dev_adarsh286 · x · https://x.com/dev_adarsh286/status/2088519979146805628 · 2026-08-15 · 21/11/2
- "New Cursor session. The agent re-suggests the same refactor you argued through last week. You paste the same architecture doc. It ignores it again." · @PowerduckLabs · x · https://x.com/PowerduckLabs/status/2108810452390310374 · 2026-10-10 · 0/1/0
- "moving between claude code and codex is where i lose the most, the new agent never knows what the last one already tried." · @AlekVectis · x · https://x.com/AlekVectis/status/2111204710623707396 · 2026-10-16 · 0/2/0
- "What gets lost on every switch is the list of things the last agent already tried. The next one starts from…" · @avibe_bot · x · https://x.com/avibe_bot/status/2104162688540532754 · 2026-09-27 · 0/0/0
- "the accountant or compliance person fixes the output, it ends up in a slack thread or some spreadsheet, and a few weeks later the agent makes the exact same mistake again" · u/Grand-Border3615 · reddit r/AI_Agents · https://www.reddit.com/r/AI_Agents/comments/1x2eegn/when_the_expert_fixes_your_agents_output_where/ · 2026-10-10 · 2 / 24
- "after working on many projects it repeats the same mistakes, uses awkward patterns or looks up stuff over and over. It just does not remember." · stuchl4n3k · hn (show hn) · https://news.ycombinator.com/item?id=49207517 · 2026-08-07 · n/a
- "I can see it make the same mistake two days running, and then months later when a new model comes out, presumably trained on my data, it still makes the same mistake." · londons_explore · hn · https://news.ycombinator.com/item?id=49981849 · 2026-10-06 · n/a
- "You approve the final diff. The agent already failed the same test a few times, skipped half the files you care about, and burned a context window doing it." · @FastfixAI · x · https://x.com/FastfixAI/status/2110527782342341098 · 2026-10-15 · 0/2/0
- "stop telling Claude Code/Codex "no, we already tried that". stop telling Claude Code/Codex "I told you this yesterday". stop telling Claude Code/Codex "I already told the other one"." · @Voxyz_ai (vendor promo) · x · https://x.com/Voxyz_ai/status/2108225911023874540 · 2026-10-08 · 29/5/3
- "Claude spent hours going in circles on my Shopify POS extension build failure: wrong theories, endless rebuilds" · @ashfaq_ulhaq · x · https://x.com/ashfaq_ulhaq/status/2087900957015511390 · 2026-08-13 · 3/1/0

## 3. handoffs drop context (agent→agent, tool→tool)
when work passes to another agent or tool, the reasoning, constraints and "what was ruled out" don't make it across.
quotes: 14 · **verdict: solves.** "handoff as a first-class artifact" is sheldon's stated differentiator. the next agent queries the graph instead of getting a prose summary, and the task board, lease and handoff live on the same graph as the evidence (REPORT §3.4, PLAN §3 items 1–2, §7 `handoff`/`resume`).

- "The first one is handoff. When one agent passes its output to the next, what it does not pass is the reasoning trace, just a summary. This makes the handoff lossy." · @arpit_bhayani · x · https://x.com/arpit_bhayani/status/2100444191876903215 · 2026-09-17 · 367/53/28
- "A planner works out "book flight to Paris under $600," writes a summary of the plan, and hands it to a booker. The summary trims the constraint. The booker gets Paris, misses the $600 ceiling, and books at $920. Both agents did exactly what they were asked." · u/Future_AGI · reddit r/AI_Agents · https://www.reddit.com/r/AI_Agents/comments/1wp2yny/multiagent_handoff_is_where_our_runs_die_whats/ · 2026-09-24 · 7 / 29
- "A researcher pulls 12 citations for a brief and hands them to a writer. The writer's context window quietly keeps 4. The other 8 fall off the tail of the prompt with no error surfaced." · same post as above
- "What actually costs me isn't the subscriptions, it's the handoff. Cursor and I work out how a module should be structured, I move the follow-up over to Claude Code, and none of that exists there. So I paste the plan again." · u/Danare_113 · reddit r/cursor · https://www.reddit.com/r/cursor/comments/1vce40y/cursor_codex_claude_code_on_the_same_repo_and_the/ · 2026-08-01 · 11 / 5
- "When a session gets too bloated and I need to pass the context to another specialised agent or a fresh session, what is the cleanest way to do this without losing critical context?" · u/oliver_dev · reddit r/AI_Agents · https://www.reddit.com/r/AI_Agents/comments/1wbifl0/how_are_you_all_handling_session_bloat_and_state/ · 2026-09-09 · 8 / 43
- "I have used one agent to implement a small change and another to review it, and the slow part was reconstructing why the first agent made a few choices." · u/BitByLiu · reddit r/cursor · https://www.reddit.com/r/cursor/comments/1uyqno7/is_a_final_diff_enough_when_multiple_tools/ · 2026-07-17 · 2 / 3
- "one committed to the wrong branch. about 2 hours to unwind, plus a revert i did not want." (lists "a handoff that is already stale") · u/ClinicalPulse · reddit r/cursor · https://www.reddit.com/r/cursor/comments/1x620iy/once_you_run_more_than_one_coding_agent_how_do/ · 2026-10-14 · 3 / 31
- "A parent agent breaks down a task. Sub-agents receive partial context. Constraints get dropped. Scope shifts. Final output can look convincing while missing requirements." · @ensydave · x · https://x.com/ensydave/status/2108575322581217360 · 2026-10-09 · 0/2/0
- "The handoff loses the policy result. The next model sees a fresh prompt with no record that the previous one declined, so a chain can drift toward whichever link says yes." · @ScottLeimroth · x · https://x.com/ScottLeimroth/status/2095541957233897490 · 2026-09-03 · 1/1/0
- "multi-agent context compaction fails silently with no error when sub-agents summarize scratchpads without write locks, so intermediate tool outputs get flattened into hallucinations that downstream workers accept as ground truth." · @RobertClapp · x · https://x.com/RobertClapp/status/2104964432166084780 · 2026-09-29 · 0/0/0
- "every handoff between agents is one more place for context to get dropped." · @tiennguyendev · x · https://x.com/tiennguyendev/status/2080465490326032577 · 2026-07-24 · 0/0/0
- "context loss is what breaks my multi-agent setups too. i log every handoff to a shared file now and the weird failures dropped a lot." · @deeponailabs · x · https://x.com/deeponailabs/status/2102783443574886792 · 2026-09-23 · 0/0/0
- "The Agent tool launches subagents successfully, and its result…" (title: "Desktop app disallows SendMessage, so subagents cannot be messaged or resumed") · @cypherair · github claude-code #92183 · https://github.com/anthropics/claude-code/issues/92183 · 2026-09-04 · 18 / 6
- "Usage-limit auto-continue doesn't resume workflows or subagents — they all fail" (issue title) · @afram123 · github claude-code #91493 · https://github.com/anthropics/claude-code/issues/91493 · 2026-09-02 · 5 / 0

## 4. runaway loops burning tokens/money
the agent hammers the same command or fix for hours and burns quota.
quotes: 10 · **verdict: partly solves.** sheldon records every action → result and can count repeats (PLAN §7, `check_prior_attempts`). but it's a memory lookup, not a loop breaker inside one run. a single agent spamming `git status` 1,435 times is only stopped if the harness checks the graph before each action. sheldon gives you the data to detect it, not an automatic kill switch.

**these quotes cite concrete numbers (see "numbers" below):**
- "wake up and find my weekly limit usage at 35% and the agent stuck in a loop running the same git status command 1435 times for the last 5 hours. I guess my harness needs a loop detector..." · @lavaze_ · x · https://x.com/lavaze_/status/2102597283531673838 · 2026-09-23 · 0/0/0
- "My cloud agent got stuck in a loop yesterday and consumed 1B tokens 😭" · @anurag__roy · x · https://x.com/anurag__roy/status/2084389289505480730 · 2026-08-03 · 0/0/0
- "We run 7 agents overnight and the 3am failures are real. Last week one got stuck in a loop burning credits for 3 hours. The automation didn't fail gracefully. It failed expensively." · @TDVEnterprises · x · https://x.com/TDVEnterprises/status/2098095252871553352 · 2026-09-10 · 0/0/0
- "i watched an agent stall on a flaky test for 40 minutes last week, retrying the same command. it burned real tokens doing nothing." · @helli0nEth · x · https://x.com/helli0nEth/status/2084065495796326427 · 2026-08-02 · 0/1/0
- "we count repeated tool errors per run and past 2 the loop stops and asks for a second opinion. most wasted tokens were the agent retrying the same wrong fix." · @kemalegebuilds · x · https://x.com/kemalegebuilds/status/2104833833392849033 · 2026-09-29 · 0/0/0
- "no matter what they kept on going in circles and did like 10 rounds of iterations (burning IDEK how many tokens) before finally settling on something" · @2014_cdj · x · https://x.com/2014_cdj/status/2088420663858016403 · 2026-08-15 · 1/0/0
- "It was stuck in a loop reading the same files over and over, and using a lot of tokens." · @norisalsaadie · x · https://x.com/norisalsaadie/status/2087293014142046346 · 2026-08-11 · 0/1/0
- "the harness keeps endlessly expanding the workflow and spawning sub-flows without reaching a resolution. It gets stuck in a loop, consumes a massive number…" · @rochawilliam · x · https://x.com/rochawilliam/status/2088010219926462798 · 2026-08-13 · 0/0/0
- "Every developer has watched their agent fall into a multi-turn trial-and-error loop over missing headers, outdated CLI flags, or missing JSON configs—burning thousands of context tokens" · @yashwant_san (vendor) · x · https://x.com/yashwant_san/status/2095387075495526427 · 2026-09-03 · 9/10/1
- "End of month bill for $8,000 for tokens because an agent went rogue or became brain-damaged and got stuck in a loop!" · @mikecane · x · https://x.com/mikecane/status/2091549016190316649 · 2026-08-23 · 1/1/0. **this one is hypothetical, not a reported bill.**

## 5. stale or corrected memory keeps getting acted on
memory holds an old or wrong fact, and the agent keeps acting on it after the user corrected it or things changed.
quotes: 13 · **verdict: partly solves (solves if Q\* ships).** source docs: events are never rewritten, hypotheses carry `status ∈ open/supported/refuted` with `SUPPORTED_BY`/`REFUTED_BY` evidence edges, and causal edges stay `proposed` until confirmed (stuff.md §4, REPORT §3.1). but the source docs **don't** describe downstream propagation, i.e. flagging open tasks or handoffs stale when a belief is refuted. that only appears in the Q\* traversal (refuted hypothesis → open tasks). if Q\* is built and demoed, this becomes "solves". sheldon also doesn't fix stale CLAUDE.md or coding-memory files outside an investigation.

- "First day I told it to use Lemon Squeezy as our MoR but second day I tell it to change to Polar. But when I ask it again, they keeps returning both answers or cannot decide which we are using." · dat999zx · hn · https://news.ycombinator.com/item?id=49399942 · 2026-08-22 · n/a
- "The migration shipped two and a half weeks ago. Nobody's thought about the queue name since. The agent isn't wrong about what it remembers — it's wrong about what it's still true." · u/Lopsided_Manner_7602 · reddit r/AI_Agents · https://www.reddit.com/r/AI_Agents/comments/1wmh2lg/why_your_agent_keeps_bringing_up_things_you/ · 2026-09-21 · 1 / 4
- "one wrong sentence poisoned Claude's memory. It kept citing itself as the source … during the first run, the source said a product pilot was announced in march claude saved it as "the product launched in march"" · @koplenkoo · x · https://x.com/koplenkoo/status/2082841500694540556 · 2026-07-30 · 17/1/1
- "Way better than keeping a giant decision file that goes stale and causes context corruption because the llm only saw the OLD decision and not the UPDATED decision." · kaydub · hn · https://news.ycombinator.com/item?id=49960779 · 2026-10-05 · n/a
- "It's like the LLMs can't just DELETE something, they always amend. So now there's stale details in there about something we abandoned polluting context." · kaydub · hn · https://news.ycombinator.com/item?id=49955890 · 2026-10-04 · n/a
- "memories go stale and pollute the context over time, especially when the state changes externally. … My most recent example were some deprecated and archived repos that kept getting added to plans for patching issues." · b-karl · hn · https://news.ycombinator.com/item?id=49952046 · 2026-10-04 · n/a
- "It’s very helpful until it scales with time, at which point it becomes useless due to staleness or mis-application across contexts." · threecheese · hn · https://news.ycombinator.com/item?id=49513521 · 2026-08-31 · n/a
- "Nobody updates the note when the decision changes two weeks later, so the file turns into a snapshot of an outdated architecture that the agent still trusts." · @Pavaniecom · x · https://x.com/Pavaniecom/status/2079011859177304572 · 2026-07-20 · 0/0/0
- "claude played pokémon and wrote one wrong memory about where it was in the game raw memory store: 5 runs out of 5 fell through the same trapdoor" · @halcyonedge (retelling an anthropic talk) · x · https://x.com/halcyonedge/status/2108612707545120969 · 2026-10-09 · 5/2/1
- "it's expensive because it keeps acting on wrong memory retrying the same thing five times because it forgot what it already learned calling apis it didn't need because stale context told it to" · @luyi_luo · x · https://x.com/luyi_luo/status/2098545365331173503 · 2026-09-11 · 0/0/0
- "A wrong memory returns: you write a second one and hope it ranks higher. The false one stays in the index." · @SoOoS16009120 · x · https://x.com/SoOoS16009120/status/2109155207611322513 · 2026-10-11 · 0/0/0
- "Vector recall degrades gradually, so you don't notice it's stale until the agent acts on a confident but wrong memory." · @jared_mitosis · x · https://x.com/jared_mitosis/status/2084612438499238064 · 2026-08-04 · 0/0/0
- "If multiple agents are reading and writing to the same memory, I'd love to be able to see which agent created a memory, which agents later retrieved it, and how it propagated across sessions. A timeline or knowledge graph of that could be really useful, especially for tracking down stale or conflicting memories." · 4nm1tsu · hn · https://news.ycombinator.com/item?id=49596312 · 2026-09-07 · n/a

## 6. can't explain why it acted / claims "done" with no evidence
no reasoning trail, no audit, and confident claims (tests pass, it's fixed) with nothing behind them.
quotes: 12 · **verdict: solves.** every sheldon answer cites event ids and returns the traversal path, inferences are labelled as inferences, and nothing becomes `confirmed` without a rule or sign-off (PLAN §1 row 5, §5.2, REPORT §3.1). **honest caveat: first-person "i asked why and it couldn't say" quotes are thin (about 4). most of this cluster is people saying audit trails matter.**

- "I asked, “Why did you delete the database?” Claude: “Sorry, I was…" · @0xZenoUsman · x · https://x.com/0xZenoUsman/status/2101332244346630467 · 2026-09-19 · 4/4/1
- "when challenged it admitted its mistake but couldn't explain why it made it. … it said it tested the change visually, but it did not even try" · cromka · hn · https://news.ycombinator.com/item?id=49881469 · 2026-09-28 · n/a
- "The agent said tests pass. Did they? You can't see its terminal. It ran the tests at some point, kept editing, then wrote "all tests pass" from memory. Or three failed and it summarised the ones that passed. Every one of those is a normal Tuesday." · @neil_xbt · x · https://x.com/neil_xbt/status/2102220336456724960 · 2026-09-22 · 46/17/11
- "Told an agent the layout looked wrong and it confidently said it was fixed. Never opened the preview. I made it take a screenshot before I believed the next one." · @Erica_Codes_NJ · x · https://x.com/Erica_Codes_NJ/status/2110414801495056841 · 2026-10-14 · 0/0/0
- "An agent would say a task was complete, but the only evidence was the agent’s own sentence." · u/Medium-Lie8127 · reddit r/AI_Agents · https://www.reddit.com/r/AI_Agents/comments/1wba3bq/the_hardest_production_failures_in_agent_systems/ · 2026-09-09 · 6 / 21
- "Then one day, Sol/High, which had been working brilliantly, started doing surprisingly dumb things. I had no idea why. It took me about a week to figure it out." · @patoistvan · x · https://x.com/patoistvan/status/2088947378602819656 · 2026-08-16 · 0/0/0
- "The audit trail is the piece most harnesses skip, and then you can't explain what the agent did three steps back." · @kyisaiah47 · x · https://x.com/kyisaiah47/status/2091972088273698957 · 2026-08-24 · 0/0/0
- "When your agent has a full computer, debugging "why did it do that" becomes distributed system tracing." · @aiwithjean · x · https://x.com/aiwithjean/status/2108664333437944191 · 2026-10-09 · 0/0/0
- "Agent actions leave no audit trail. The question isn't "can LLMs do useful work?" anymore. It's "why did it delete that folder?"" · @skyrain888 · x · https://x.com/skyrain888/status/2079360369584439404 · 2026-07-21 · 0/0/0
- "Your incident report has a root cause of "unknown" because nobody logged the tool calls. … They don't tell you why it decided to wire $1.7B in ETH to the wrong address." · @pulpmatrix · x · https://x.com/pulpmatrix/status/2096599342761275883 · 2026-09-06 · 0/1/0
- "developers have almost no visibility into: … **When** memory entries get stale, overwritten, or poisoned - **Why** an agent made a particular decision based on memory context" · @DijieDeng · github crewAI #7352 · https://github.com/crewAIInc/crewAI/issues/7352 · 2026-09-09 · 0 / 0
- "Git has the code; the missing piece is the reasoning trail. … Without it you re-debate decisions" · @sisiliu517 · x · https://x.com/sisiliu517/status/2111117369296720239 · 2026-10-16 · 0/0/0

## 7. on-call / incident pain with ai tools
ai sre and on-call tools that send responders down the wrong path, can't show reasoning, or lose what was ruled out between shifts.
quotes: 9 · **verdict: partly solves.** sheldon *is* incident-investigation memory: hypotheses, evidence, what was ruled out, and handoff between responders/agents (REPORT §4). it doesn't detect, correlate alerts, act on prod, or speed up triage. it covers the "what did we already try / why do we believe this" part only.

- "An AI SRE that can't show its reasoning trail is just a faster way to be confidently wrong at 3am. Curious how the evidence trail is retained for post-incident review." · @_malcolmadams · x · https://x.com/_malcolmadams/status/2108748636498858140 · 2026-10-10 · 0/0/0
- "This is the agent version of a bad on-call handoff — happens when incidents get passed along without writing down what's already ruled out. … No durable state means the next person redoes the work." · @survivesprod · x · https://x.com/survivesprod/status/2082511400866361835 · 2026-07-29 · 0/1/0
- "If the judge's baseline is weak, you don't just get a bad summary, you send the on call down the wrong path while the customer is still down...." · @Vatsalpandya333 · x · https://x.com/Vatsalpandya333/status/2096045243103887512 · 2026-09-05 · 1/0/0
- "We turned off the auto-restart after it restarted the wrong service during a partial outage and turned a ten-minute…" · @loneman_v_0_2 · x · https://x.com/loneman_v_0_2/status/2095085306999390599 · 2026-09-02 · 81/37/6
- "an on-call engineer gets an issue say at 2 AM and there's no context. No idea about -What broke? -Whose problem is it? -Where do I even start?" · @notbhuvanesh (builder) · x · https://x.com/notbhuvanesh/status/2100876128127000958 · 2026-09-18 · 1/0/0
- "The on-call still rebuilds it all from Slack at 3 a.m." · @polsia (builder) · x · https://x.com/polsia/status/2090501206628319355 · 2026-08-20 · 0/0/0
- "Every AI SRE tool got good at one thing this year: correlating signals faster, drafting a tidier incident summary, writing the timeline nobody wanted to write at 3am. None of that tells you why it broke." · @SourabhkKumawat (vendor) · x · https://x.com/SourabhkKumawat/status/2094673111937352055 · 2026-09-01 · 1/0/0
- "someone gets paged on a symptom, p99 latency up, error rate up, saturation, and jumps through dashboards, traces, logs, feature flags, and deploy history, spending the next half hour or so just correlating the spike with the code path and the recent changes behind it." · u/Most_Development_947 · reddit r/sre · https://www.reddit.com/r/sre/comments/1vbw55w/why_is_high_mttr_despite_observability_stack/ · 2026-07-31 · 0 / 6
- "Getting that on-call incident for a piece of code I own, when i've lost the mental map of what the black box does, it keeps me up at night." · Joe_Boogz · hn · https://news.ycombinator.com/item?id=49851589 · 2026-09-25 · n/a

## 8. destructive actions in prod (side note)
agents deleting prod data in-window.
quotes: 4 · **verdict: doesn't touch.** sheldon is memory + coordination for investigations. it has no permission gating or action sandboxing. (`GRAPH.COPY` speculative runs only sandbox the graph, not prod.)

- "Your own AI agent deleted ALL my production database data on July 18 — 52 tables wiped, all customers, orders and financial records gone." · @silverlusilver · x · https://x.com/silverlusilver/status/2078874502826475835 · 2026-07-19 · 1/1/0
- "ChatGPT Codex deleted our SudoClone production database. Over 700 users (12 Pro users), more than 3,000 processed messages, and all payment details were wiped." · @SudotechLimited · x · https://x.com/SudotechLimited/status/2093261737218777555 · 2026-08-28 · 1/0/0
- "I asked Claude to create a test migration in one step. Somehow, it hallucinated and deleted the entire database." · @0xZenoUsman · x · https://x.com/0xZenoUsman/status/2101332244346630467 · 2026-09-19 · 4/4/1 (also in 6)
- "A developer ran Opus 5 on Ultracode against a Supabase project. Ten minutes later, every table was empty." · @SlavaOPs · x · https://x.com/SlavaOPs/status/2082540248089624772 · 2026-07-29 · 3/1/0

---

## pitch mapping: a / b / c

**(a) a belief only changes status when it cites evidence** → clusters 6, 5
- @neil_xbt "then wrote "all tests pass" from memory" (2026-09-22, 46 likes) https://x.com/neil_xbt/status/2102220336456724960
- u/Medium-Lie8127 "the only evidence was the agent’s own sentence" (2026-09-09) https://www.reddit.com/r/AI_Agents/comments/1wba3bq/the_hardest_production_failures_in_agent_systems/
- @Erica_Codes_NJ "it confidently said it was fixed. Never opened the preview." (2026-10-14) https://x.com/Erica_Codes_NJ/status/2110414801495056841
- @koplenkoo "It kept citing itself as the source" (2026-07-30, 17 likes) https://x.com/koplenkoo/status/2082841500694540556. an unsupported belief got promoted to "fact", which is exactly what the citation gate blocks.
- cromka "it said it tested the change visually, but it did not even try" (2026-09-28) https://news.ycombinator.com/item?id=49881469
- @_malcolmadams "An AI SRE that can't show its reasoning trail is just a faster way to be confidently wrong at 3am." (2026-10-10)

**(b) when a belief is refuted, downstream tasks/handoffs get flagged stale** → cluster 5 (plus 3)
- u/Lopsided_Manner_7602: the agent kept raising a blocker that had been resolved weeks earlier: "The agent isn't wrong about what it remembers — it's wrong about what it's still true." (2026-09-21). best (b) quote: a stale *task/blocker*, not just a stale fact.
- dat999zx: Lemon Squeezy → Polar, "they keeps returning both answers or cannot decide which we are using" (2026-08-22)
- kaydub: "the llm only saw the OLD decision and not the UPDATED decision" (2026-10-05)
- b-karl: "deprecated and archived repos that kept getting added to plans" (2026-10-04). stale info flowing into *plans*.
- u/ClinicalPulse lists "a handoff that is already stale" as a top multi-agent pain (2026-10-14)
- @Pavaniecom: "a snapshot of an outdated architecture that the agent still trusts" (2026-07-20)
- caveat: nobody in the window described downstream propagation in those exact words. people describe the symptom (old belief keeps steering plans/tasks), not the mechanism.

**(c) measured count of repeated failed steps vs plain memory** → clusters 2, 4
- @lavaze_ "the same git status command 1435 times for the last 5 hours", 35% of the weekly limit (2026-09-23)
- @anurag__roy "consumed 1B tokens" (2026-08-03)
- @TDVEnterprises "stuck in a loop burning credits for 3 hours" (2026-09-10)
- @helli0nEth "40 minutes … retrying the same command" (2026-08-02)
- @sunsetsyntax "we lost a day once because the second agent retried the same broken approach" (2026-09-29)
- @kemalegebuilds already counts repeats: "we count repeated tool errors per run and past 2 the loop stops … most wasted tokens were the agent retrying the same wrong fix." (2026-09-29). proof that practitioners want this metric.
- @halcyonedge: wrong memory → "5 runs out of 5 fell through the same trapdoor" (2026-10-09, retelling an anthropic talk). directly relevant to "with memory vs plain memory".

### numbers people cited for repeated failed steps (for the report)
| number | who | link | date |
|---|---|---|---|
| same `git status` 1,435× over 5 h, 35% of weekly limit | @lavaze_ | https://x.com/lavaze_/status/2102597283531673838 | 2026-09-23 |
| 1B tokens in one stuck loop | @anurag__roy | https://x.com/anurag__roy/status/2084389289505480730 | 2026-08-03 |
| 3 h loop burning credits (7 overnight agents) | @TDVEnterprises | https://x.com/TDVEnterprises/status/2098095252871553352 | 2026-09-10 |
| 40 min retrying same command on flaky test | @helli0nEth | https://x.com/helli0nEth/status/2084065495796326427 | 2026-08-02 |
| ~10 rounds of codex↔claude iterations | @2014_cdj | https://x.com/2014_cdj/status/2088420663858016403 | 2026-08-15 |
| lost a day to a retried broken approach after handoff | @sunsetsyntax | https://x.com/sunsetsyntax/status/2104832764407087549 | 2026-09-29 |
| 5/5 runs hit the same trapdoor from one wrong memory | @halcyonedge | https://x.com/halcyonedge/status/2108612707545120969 | 2026-10-09 |
| "$8,000" monthly bill: **hypothetical**, don't cite as real | @mikecane | https://x.com/mikecane/status/2091549016190316649 | 2026-08-23 |

---

## best pitch ammo
1. "within a few turns Claude proposes something we already tried and threw out two hours earlier." · u/Prestigious_Grape786 · https://www.reddit.com/r/ClaudeAI/comments/1vwy3hw/compaction_keeps_what_we_built_and_forgets_what/ · 2026-08-24
2. "the agent stuck in a loop running the same git status command 1435 times for the last 5 hours." · @lavaze_ · https://x.com/lavaze_/status/2102597283531673838 · 2026-09-23
3. "When one agent passes its output to the next, what it does not pass is the reasoning trace, just a summary. This makes the handoff lossy." · @arpit_bhayani · https://x.com/arpit_bhayani/status/2100444191876903215 · 2026-09-17 · 367 likes
4. "An AI SRE that can't show its reasoning trail is just a faster way to be confidently wrong at 3am." · @_malcolmadams · https://x.com/_malcolmadams/status/2108748636498858140 · 2026-10-10
5. "The agent isn't wrong about what it remembers — it's wrong about what it's still true." · u/Lopsided_Manner_7602 · https://www.reddit.com/r/AI_Agents/comments/1wmh2lg/why_your_agent_keeps_bringing_up_things_you/ · 2026-09-21

---

## read after: notes
- a lot of x posts in clusters 1–3 come from people selling memory tools (claude-mem, projectmem, beacon, funes and others). i kept a few promos only where the pain line stands alone and marked them "vendor"/"builder". first-person complaints were preferred.
- github: claude-code has many in-window compaction/subagent issues. langgraph/autogen/mem0/letta issues are mostly low-level bugs with no quotable pain (0–2 reactions). crewai #7352 is the only framework issue that names stale/poisoned memory + "why".
- reddit: reddit.com and old.reddit json are blocked from the box (403/login wall). i used arctic-shift (an archive api) for search and created_utc. r/LocalLLaMA, r/LangChain, r/devops searches returned little that was relevant in the time i had.
- hn: plenty of volume, but most "incident" hits are about ai-safety incidents (hf hack and similar), not on-call pain. on-call quotes are mostly x.
- not done: a second pass on papers (out of scope).
