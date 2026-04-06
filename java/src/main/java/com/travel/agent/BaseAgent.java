package com.travel.agent;

import com.travel.model.TravelPlanState;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 智能体抽象基类：模板方法模式（Template Method）。
 * <p>
 * {@link #run(TravelPlanState)} 固定骨架（日志、扩展点可加入计时/熔断），
 * {@link #execute(TravelPlanState)} 由子类实现具体业务。
 * </p>
 * <p>
 * 面试要点：与「策略模式」区别——模板方法强调算法步骤不可变、部分步骤可覆盖；
 * 若把 Agent 换成接口 + 多实现，则更偏策略（可互换算法）。
 * </p>
 */
public abstract class BaseAgent {

    protected final Logger log = LoggerFactory.getLogger(getClass());

    /**
     * 对外入口：先记录上下文再执行子类逻辑。
     */
    public final void run(TravelPlanState state) {
        log.debug("Agent [{}] 开始执行，当前状态={}", getClass().getSimpleName(), state.getPlanningState());
        execute(state);
        log.debug("Agent [{}] 执行结束", getClass().getSimpleName());
    }

    /**
     * 子类实现的核心逻辑。
     */
    protected abstract void execute(TravelPlanState state);
}
